"""
OpenClaw agent execution helpers for PinchBench.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import stat
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import error, request

from lib_paths import agent_model_workspace, agent_task_workspace
from lib_tasks import Task


logger = logging.getLogger(__name__)

USE_SHELL = platform.system() == "Windows"


class ModelValidationError(Exception):
    """Raised when a model ID is invalid or inaccessible."""

    pass


MAX_OPENCLAW_MESSAGE_CHARS = int(os.environ.get("PINCHBENCH_MAX_MSG_CHARS", "8000"))
JUDGE_MAX_MSG_CHARS = int(os.environ.get("PINCHBENCH_JUDGE_MAX_MSG_CHARS", "3000"))


def _coerce_subprocess_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def slugify_model(model_id: str) -> str:
    return model_id.replace("/", "-").replace(".", "-").lower()


def validate_openrouter_model(model_id: str, timeout_seconds: float = 10.0) -> bool:
    """
    Validate that a model ID exists on OpenRouter.

    Args:
        model_id: Model ID (with or without openrouter/ prefix)
        timeout_seconds: HTTP request timeout

    Returns:
        True if model is valid and accessible

    Raises:
        ModelValidationError: If model doesn't exist or validation fails
    """
    # Strip openrouter/ prefix if present
    bare_model_id = model_id
    if bare_model_id.startswith("openrouter/"):
        bare_model_id = bare_model_id[len("openrouter/") :]

    # Skip validation for non-OpenRouter models
    if "/" not in bare_model_id:
        logger.info("Skipping model validation for non-OpenRouter model: %s", model_id)
        return True

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not set, skipping model validation")
        return True

    logger.info("🔍 Validating model: %s", bare_model_id)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://pinchbench.com",
        "X-Title": "PinchBench",
    }

    # First, try the specific model endpoint (fast path for valid models)
    encoded_model_id = bare_model_id.replace("/", "%2F")
    specific_endpoint = f"https://openrouter.ai/api/v1/models/{encoded_model_id}"
    req = request.Request(specific_endpoint, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            # Model exists - validation passed
            logger.info("✅ Model validated: %s", bare_model_id)
            return True
    except error.HTTPError as exc:
        if exc.code == 404:
            # Model not found - fall through to fetch full catalog for suggestions
            pass
        else:
            logger.warning("OpenRouter API error during validation: %s", exc)
            return True
    except error.URLError as exc:
        logger.warning("Network error during model validation: %s", exc)
        return True

    # Model not found - fetch full catalog for "did you mean" suggestions
    catalog_endpoint = "https://openrouter.ai/api/v1/models"
    req = request.Request(catalog_endpoint, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        logger.warning("OpenRouter API error fetching model catalog: %s", exc)
        raise ModelValidationError(f"Model '{bare_model_id}' not found on OpenRouter.")
    except error.URLError as exc:
        logger.warning("Network error fetching model catalog: %s", exc)
        raise ModelValidationError(f"Model '{bare_model_id}' not found on OpenRouter.")
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse OpenRouter response: %s", exc)
        raise ModelValidationError(f"Model '{bare_model_id}' not found on OpenRouter.")

    models = data.get("data", [])
    model_ids = {
        mid
        for m in models
        if isinstance(m, dict)
        for mid in [m.get("id")]
        if isinstance(mid, str) and mid
    }

    # Some OpenRouter model detail lookups intermittently return 404 for valid
    # IDs. Treat an exact catalog hit as authoritative to avoid false negatives.
    if bare_model_id in model_ids:
        logger.info("✅ Model validated via catalog fallback: %s", bare_model_id)
        return True

    # Check for close matches (typos)
    close_matches = []
    bare_lower = bare_model_id.lower()
    for mid in model_ids:
        mid_lower = mid.lower()
        if mid_lower == bare_lower:
            continue
        if bare_lower in mid_lower or mid_lower in bare_lower:
            close_matches.append(mid)

    error_msg = f"Model '{bare_model_id}' not found on OpenRouter."
    if close_matches:
        close_matches_str = ", ".join(sorted(close_matches)[:5])
        error_msg += f" Did you mean: {close_matches_str}?"
    else:
        # Try to suggest based on provider
        provider = bare_model_id.split("/")[0] if "/" in bare_model_id else None
        if provider:
            provider_models = [m for m in model_ids if m.startswith(f"{provider}/")]
            if provider_models:
                error_msg += (
                    f" Available {provider} models: {', '.join(sorted(provider_models)[:5])}"
                )

    raise ModelValidationError(error_msg)


def _get_agent_workspace(agent_id: str) -> Path | None:
    """Get the workspace path for an agent from the local OpenClaw store."""
    agent_dir = _get_agent_store_dir(agent_id)
    metadata_path = agent_dir / "agent" / "workspace.json"
    if metadata_path.exists():
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read workspace metadata for %s: %s", agent_id, exc)
        else:
            workspace_dir = payload.get("workspaceDir")
            if isinstance(workspace_dir, str) and workspace_dir.strip():
                return Path(workspace_dir)
    sessions_store = agent_dir / "sessions" / "sessions.json"
    if not sessions_store.exists():
        return None
    try:
        sessions_payload = json.loads(sessions_store.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read sessions store for %s: %s", agent_id, exc)
        return None
    if not isinstance(sessions_payload, dict):
        return None

    def _to_path(value: Any) -> Path | None:
        if not isinstance(value, str) or not value.strip():
            return None
        workspace_str = value.strip()
        if workspace_str.startswith("~/"):
            workspace_str = str(Path.home() / workspace_str[2:])
        return Path(workspace_str)

    def _extract_workspace(entry: Any) -> Path | None:
        if not isinstance(entry, dict):
            return None
        direct_path = _to_path(entry.get("workspaceDir"))
        if direct_path is not None:
            return direct_path
        system_report = entry.get("systemPromptReport")
        if isinstance(system_report, dict):
            report_path = _to_path(system_report.get("workspaceDir"))
            if report_path is not None:
                return report_path
        return None

    normalized_id = agent_id.replace(":", "-").lower()
    preferred_keys = [
        f"agent:{agent_id}:main",
        f"agent:{agent_id}:default",
        f"agent:{normalized_id}:main",
        f"agent:{normalized_id}:default",
    ]
    for key in preferred_keys:
        workspace = _extract_workspace(sessions_payload.get(key))
        if workspace is not None:
            return workspace

    newest_workspace = None
    newest_timestamp = -1
    for entry in sessions_payload.values():
        workspace = _extract_workspace(entry)
        if workspace is None or not isinstance(entry, dict):
            continue
        updated_at = entry.get("updatedAt")
        if isinstance(updated_at, (int, float)) and updated_at > newest_timestamp:
            newest_timestamp = updated_at
            newest_workspace = workspace
        elif newest_workspace is None:
            newest_workspace = workspace
    return newest_workspace


def _remove_agent_store(agent_id: str) -> None:
    """Remove local agent store directories for an agent."""
    base_dir = Path.home() / ".openclaw" / "agents"
    normalized_id = agent_id.replace(":", "-").lower()
    candidates = [base_dir / agent_id]
    normalized_dir = base_dir / normalized_id
    if normalized_dir not in candidates:
        candidates.append(normalized_dir)
    for path in candidates:
        if not path.exists():
            continue
        try:
            shutil.rmtree(path)
        except OSError as exc:
            logger.warning("Failed to remove local agent store %s: %s", path, exc)


def _write_agent_workspace_metadata(agent_id: str, workspace_dir: Path) -> None:
    metadata_path = _get_agent_store_dir(agent_id) / "agent" / "workspace.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        metadata_path.write_text(
            json.dumps({"workspaceDir": str(workspace_dir)}, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("Failed to write workspace metadata for %s: %s", agent_id, exc)


def ensure_agent_exists(
    agent_id: str,
    model_id: str,
    workspace_dir: Path,
    *,
    base_url: str | None = None,
    api_key: str | None = None,
) -> bool:
    """Ensure the OpenClaw agent exists with the correct workspace.

    If the agent already exists but points to a different workspace, it is
    deleted and recreated so that the new workspace takes effect.

    When *base_url* is provided, a custom OpenAI-compatible provider is
    configured in the agent's ``models.json`` instead of relying on
    OpenRouter.  *api_key* defaults to ``${OPENAI_API_KEY}`` (resolved by
    OpenClaw at runtime) if not given.

    Returns True if the agent was (re)created.
    """
    workspace_dir.mkdir(parents=True, exist_ok=True)

    agent_store_dir = _get_agent_store_dir(agent_id)
    if (agent_store_dir / "agent").exists():
        current_workspace = _get_agent_workspace(agent_id)
        if current_workspace is not None and current_workspace.resolve() == workspace_dir.resolve():
            logger.info("Agent %s already exists with correct workspace", agent_id)
            _write_agent_workspace_metadata(agent_id, workspace_dir)
            return False
        logger.info(
            "Agent %s exists with stale workspace (%s != %s), recreating",
            agent_id,
            current_workspace,
            workspace_dir,
        )
        subprocess.run(
            ["openclaw", "agents", "delete", agent_id, "--force"],
            capture_output=True,
            text=True,
            check=False,
            shell=USE_SHELL,
        )
        _remove_agent_store(agent_id)

    logger.info("Creating OpenClaw agent %s", agent_id)
    try:
        create_result = subprocess.run(
            [
                "openclaw",
                "agents",
                "add",
                agent_id,
                "--model",
                model_id,
                "--workspace",
                str(workspace_dir),
                "--non-interactive",
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=USE_SHELL,
        )
    except FileNotFoundError:
        logger.error("openclaw CLI not found while creating agent")
        return False

    if create_result.returncode != 0:
        logger.warning(
            "Agent creation returned %s: %s", create_result.returncode, create_result.stderr
        )
        already_exists_text = f'Agent "{agent_id}" already exists.'
        if already_exists_text in (create_result.stdout or "") or already_exists_text in (
            create_result.stderr or ""
        ):
            subprocess.run(
                ["openclaw", "agents", "delete", agent_id, "--force"],
                capture_output=True,
                text=True,
                check=False,
                shell=USE_SHELL,
            )
            _remove_agent_store(agent_id)
            create_result = subprocess.run(
                [
                    "openclaw",
                    "agents",
                    "add",
                    agent_id,
                    "--model",
                    model_id,
                    "--workspace",
                    str(workspace_dir),
                    "--non-interactive",
                ],
                capture_output=True,
                text=True,
                check=False,
                shell=USE_SHELL,
            )
            if create_result.returncode != 0:
                logger.warning(
                    "Agent recreation returned %s: %s",
                    create_result.returncode,
                    create_result.stderr,
                )

    # Configure models.json for the bench agent
    bench_agent_dir = _get_agent_store_dir(agent_id) / "agent"
    bench_agent_dir.mkdir(parents=True, exist_ok=True)
    bench_models = bench_agent_dir / "models.json"
    main_models = Path.home() / ".openclaw" / "agents" / "main" / "agent" / "models.json"

    if base_url:
        # Custom OpenAI-compatible endpoint — build a provider entry
        data: dict[str, Any] = {}
        if main_models.exists():
            try:
                data = json.loads(main_models.read_text("utf-8-sig"))
            except (json.JSONDecodeError, OSError):
                data = {}

        key_ref = api_key if api_key else "${OPENAI_API_KEY}"
        providers = data.setdefault("models", {}).setdefault("providers", {})
        data["models"]["mode"] = "merge"
        providers["custom"] = {
            "baseUrl": base_url,
            "apiKey": key_ref,
            "api": "openai-completions",
            "models": [
                {
                    "id": model_id,
                    "name": model_id,
                    "reasoning": False,
                    "input": ["text"],
                    "contextWindow": 200000,
                    "maxTokens": 8192,
                }
            ],
        }
        data["defaultProvider"] = "custom"
        data["defaultModel"] = model_id
        bench_models.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
        logger.info(
            "Configured custom provider (%s) with model %s for agent %s",
            base_url,
            model_id,
            agent_id,
        )
    elif main_models.exists():
        # Standard OpenRouter flow — copy main's models.json and set defaults
        import shutil as _shutil
        _shutil.copy2(main_models, bench_models)
        if "/" in model_id:
            provider_name, model_name = model_id.split("/", 1)
            try:
                raw = bench_models.read_text("utf-8-sig")
                data = json.loads(raw)
                data["defaultProvider"] = provider_name
                data["defaultModel"] = model_name
                bench_models.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), "utf-8"
                )
                logger.info(
                    "Set bench agent default model to %s / %s", provider_name, model_name
                )
            except Exception as exc:
                logger.warning("Failed to set default model in bench models.json: %s", exc)
        logger.info("Copied main agent models.json to bench agent %s", agent_id)

    # Delete sessions.json so OpenClaw picks up the new defaultProvider/defaultModel
    # instead of reusing a cached session entry that still points to an old model.
    bench_sessions_dir = _get_agent_store_dir(agent_id) / "sessions"
    sessions_store = bench_sessions_dir / "sessions.json"
    if sessions_store.exists():
        try:
            sessions_store.unlink()
            logger.info("Deleted stale sessions.json for bench agent %s", agent_id)
        except OSError as exc:
            logger.warning("Failed to delete sessions.json: %s", exc)

    _write_agent_workspace_metadata(agent_id, workspace_dir)
    return True


def cleanup_agent_sessions(agent_id: str) -> None:
    """Remove stored session transcripts for an agent to avoid unbounded growth."""
    agent_dir = _get_agent_store_dir(agent_id)
    sessions_dir = agent_dir / "sessions"
    if not sessions_dir.exists():
        return
    removed = 0
    for pattern in ("*.jsonl", "*.jsonl.lock", "*.ndjson"):
        for path in sessions_dir.rglob(pattern):
            try:
                path.unlink()
                removed += 1
            except OSError as exc:
                logger.warning("Failed to remove session file %s: %s", path, exc)
    sessions_store = sessions_dir / "sessions.json"
    if sessions_store.exists():
        try:
            sessions_store.unlink()
        except OSError as exc:
            logger.warning("Failed to remove session store %s: %s", sessions_store, exc)
    if removed:
        logger.info("Removed %s old OpenClaw session transcripts for %s", removed, agent_id)


def prepare_task_workspace(skill_dir: Path, run_id: str, task: Task, agent_id: str) -> Path:
    """
    Prepare workspace for a task by copying fixtures.
    Uses the agent's configured workspace to ensure files are in the right place.
    """
    import shutil

    # Get agent's workspace from agent config.
    # In single-agent-per-model mode, OpenClaw writes are scoped to the configured
    # agent workspaceDir (not subprocess cwd). We keep using that same workspace.
    workspace_base = _get_agent_workspace(agent_id)
    if workspace_base is None:
        # Fallback to model-root workspace so grading path matches OpenClaw writes.
        logger.warning("Could not find agent workspace metadata, using model workspace fallback")
        model_slug = os.environ.get("PINCHBENCH_MODEL_SLUG")
        scope = os.environ.get("PINCHBENCH_RUN_SCOPE", "formal")
        if model_slug:
            workspace = agent_model_workspace(scope, model_slug)
        else:
            workspace = Path(f"/tmp/pinchbench/{run_id}/{task.task_id}")
    else:
        workspace = workspace_base

    _BOOTSTRAP_FILES = ["SOUL.md", "BOOTSTRAP.md", "USER.md", "IDENTITY.md", "HEARTBEAT.md", "TOOLS.md"]

    def _remove_readonly(func, path, _):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            pass

    saved_bootstrap: dict[str, bytes] = {}
    if workspace.exists():
        for fname in _BOOTSTRAP_FILES:
            fpath = workspace / fname
            if fpath.exists():
                saved_bootstrap[fname] = fpath.read_bytes()
        shutil.rmtree(workspace, onerror=_remove_readonly)
    workspace.mkdir(parents=True, exist_ok=True)

    for fname, content in saved_bootstrap.items():
        (workspace / fname).write_bytes(content)

    for file_spec in task.workspace_files:
        if "content" in file_spec:
            dest = workspace / file_spec["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(file_spec["content"])
            continue

        source = skill_dir / "assets" / file_spec["source"]
        dest = workspace / file_spec["dest"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.write_bytes(source.read_bytes())
        except FileNotFoundError:
            logger.error("Workspace file not found: %s", source)
            raise

    # [MODIFIED] Removed blanket skill copying logic that was here originally.
    # The original code copied all skills from ~/.openclaw/workspace/skills/ into
    # every task's benchmark workspace, regardless of whether the task needed them.
    # This caused two problems:
    #   1. Wasted time copying unrelated skills on every task.
    #   2. Exposed agents to irrelevant tools, potentially confusing their decisions.
    #      (e.g. task_14_humanizer explicitly tests whether the agent can install a
    #       skill on its own — pre-copying skills breaks that test.)
    # If a task genuinely requires a specific skill, declare it in the task's
    # frontmatter via a `required_skills` field and add copying logic here.

    return workspace


def _get_agent_store_dir(agent_id: str) -> Path:
    base_dir = Path.home() / ".openclaw" / "agents"
    # OpenClaw normalizes agent IDs to lowercase and replaces colons with dashes
    normalized_id = agent_id.replace(":", "-").lower()
    direct_dir = base_dir / agent_id
    if direct_dir.exists():
        return direct_dir
    normalized_dir = base_dir / normalized_id
    if normalized_dir.exists():
        return normalized_dir
    return direct_dir


def _resolve_session_id_from_store(agent_id: str) -> str | None:
    agent_dir = _get_agent_store_dir(agent_id)
    sessions_store = agent_dir / "sessions" / "sessions.json"
    if not sessions_store.exists():
        return None
    try:
        sessions_payload = json.loads(sessions_store.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse sessions store: %s", exc)
        return None
    if not isinstance(sessions_payload, dict):
        return None

    normalized_id = agent_id.replace(":", "-").lower()
    preferred_keys = [
        f"agent:{agent_id}:main",
        f"agent:{agent_id}:default",
        f"agent:{normalized_id}:main",
        f"agent:{normalized_id}:default",
    ]
    for key in preferred_keys:
        entry = sessions_payload.get(key)
        if isinstance(entry, dict) and entry.get("sessionId"):
            return entry["sessionId"]

    newest_entry = None
    newest_timestamp = -1
    for entry in sessions_payload.values():
        if not isinstance(entry, dict):
            continue
        if "sessionId" not in entry:
            continue
        updated_at = entry.get("updatedAt")
        if isinstance(updated_at, (int, float)) and updated_at > newest_timestamp:
            newest_timestamp = updated_at
            newest_entry = entry
    if newest_entry:
        return newest_entry.get("sessionId")
    return None


def _find_transcript_path_from_sessions_store(agent_id: str) -> Optional[Path]:
    """Best-effort transcript path resolution from sessions.json payload values."""
    agent_dir = _get_agent_store_dir(agent_id)
    sessions_store = agent_dir / "sessions" / "sessions.json"
    if not sessions_store.exists():
        return None
    try:
        payload = json.loads(sessions_store.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None

    def _iter_strings(node: Any):
        if isinstance(node, str):
            yield node
        elif isinstance(node, dict):
            for value in node.values():
                yield from _iter_strings(value)
        elif isinstance(node, list):
            for value in node:
                yield from _iter_strings(value)

    suffixes = (".jsonl", ".ndjson")
    session_root = agent_dir / "sessions"
    for value in _iter_strings(payload):
        if not value.endswith(suffixes):
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = session_root / value
        if candidate.exists():
            return candidate
    return None


def _find_recent_session_path(agent_dir: Path, started_at: float) -> Path | None:
    sessions_dir = agent_dir / "sessions"
    if not sessions_dir.exists():
        return None
    candidates = list(sessions_dir.rglob("*.jsonl")) + list(sessions_dir.rglob("*.ndjson"))
    if not candidates:
        return None
    tolerance_seconds = 5.0
    recent_candidates = [
        path for path in candidates if path.stat().st_mtime >= (started_at - tolerance_seconds)
    ]
    pool = recent_candidates or candidates
    return max(pool, key=lambda path: path.stat().st_mtime)


def _pending_transcript_lock_paths(agent_dir: Path, resolved_session_id: str | None) -> List[Path]:
    """Return lock files that indicate OpenClaw is still flushing transcript data."""
    sessions_dir = agent_dir / "sessions"
    if not sessions_dir.exists():
        return []

    candidates: List[Path] = []
    if resolved_session_id:
        direct_lock = sessions_dir / f"{resolved_session_id}.jsonl.lock"
        if direct_lock.exists():
            candidates.append(direct_lock)

        nested_lock = sessions_dir / resolved_session_id / "transcript.jsonl.lock"
        if nested_lock.exists():
            candidates.append(nested_lock)

        nested_events_lock = sessions_dir / resolved_session_id / "events.jsonl.lock"
        if nested_events_lock.exists():
            candidates.append(nested_events_lock)

    if candidates:
        return candidates

    return list(sessions_dir.rglob("*.jsonl.lock"))


def _load_transcript(
    agent_id: str, session_id: str, started_at: float
) -> tuple[List[Dict[str, Any]], Optional[Path]]:
    agent_dir = _get_agent_store_dir(agent_id)
    transcript_path = None

    # OpenClaw ignores the --session-id we pass and generates its own UUID-based
    # session ID internally.  We need to discover the actual transcript path.
    #
    # Strategy (with retries to handle write-delay):
    #   1. Resolve the real session ID from sessions.json
    #   2. Glob for any .jsonl in the sessions dir (most-recently-modified)
    #   3. Try our passed-in session ID as a last resort
    max_attempts = 45
    for attempt in range(max_attempts):
        # 1. Try sessions.json first — OpenClaw writes the real UUID here
        resolved_session_id = _resolve_session_id_from_store(agent_id)
        if resolved_session_id:
            session_dir = agent_dir / "sessions"
            for candidate in (
                session_dir / f"{resolved_session_id}.jsonl",
                session_dir / f"{resolved_session_id}.ndjson",
                session_dir / resolved_session_id / "transcript.jsonl",
                session_dir / resolved_session_id / "events.jsonl",
            ):
                if candidate.exists():
                    transcript_path = candidate
                    logger.info(
                        "Found transcript via sessions.json: %s (attempt %s)",
                        candidate.name,
                        attempt + 1,
                    )
                    break
            if transcript_path is not None:
                break

        # 1b. Parse transcript-like paths from sessions.json values
        candidate_from_store = _find_transcript_path_from_sessions_store(agent_id)
        if candidate_from_store is not None:
            transcript_path = candidate_from_store
            logger.info(
                "Found transcript via sessions.json path: %s (attempt %s)",
                candidate_from_store,
                attempt + 1,
            )
            break

        # 2. Glob fallback — pick the most recently modified .jsonl
        recent_path = _find_recent_session_path(agent_dir, started_at)
        if recent_path is not None:
            transcript_path = recent_path
            logger.info(
                "Found transcript via glob fallback: %s (attempt %s)",
                recent_path.name,
                attempt + 1,
            )
            break

        # 3. Try our passed-in session ID (unlikely to work, but check anyway)
        for direct_path in (
            agent_dir / "sessions" / f"{session_id}.jsonl",
            agent_dir / "sessions" / f"{session_id}.ndjson",
        ):
            if direct_path.exists():
                transcript_path = direct_path
                logger.info(
                    "Found transcript via passed session ID: %s (attempt %s)",
                    direct_path.name,
                    attempt + 1,
                )
                break
        if transcript_path is not None:
            break

        pending_locks = _pending_transcript_lock_paths(agent_dir, resolved_session_id)
        if pending_locks and attempt < max_attempts - 1:
            if attempt in (0, 4, 14, 29):
                logger.info(
                    "Waiting for transcript lock to clear for %s: %s (attempt %s/%s)",
                    agent_id,
                    [path.name for path in pending_locks],
                    attempt + 1,
                    max_attempts,
                )
            time.sleep(2.0)
            continue

        if attempt < max_attempts - 1:
            time.sleep(1.0)

    if transcript_path is None:
        sessions_dir = agent_dir / "sessions"
        if sessions_dir.exists():
            all_files = list(sessions_dir.iterdir())
            logger.warning(
                "Transcript not found for agent %s. Sessions dir contents: %s",
                agent_id,
                [f.name for f in all_files],
            )
            sessions_store = sessions_dir / "sessions.json"
            if sessions_store.exists():
                try:
                    payload_preview = sessions_store.read_text(encoding="utf-8")[:1200]
                    logger.warning("sessions.json preview: %s", payload_preview)
                except OSError as exc:
                    logger.warning("Could not read sessions.json preview: %s", exc)
        else:
            logger.warning(
                "Transcript not found — sessions dir does not exist: %s",
                sessions_dir,
            )
        return [], None

    transcript: List[Dict[str, Any]] = []
    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            transcript.append(json.loads(line))
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse transcript line: %s", exc)
            transcript.append({"raw": line, "parse_error": str(exc)})
    return transcript, transcript_path


def _extract_usage_from_transcript(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Sum token usage and cost from all assistant messages in transcript."""
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "request_count": 0,
    }

    for entry in transcript:
        if entry.get("type") != "message":
            continue
        msg = entry.get("message", {})
        if msg.get("role") != "assistant":
            continue
        totals["request_count"] += 1
        usage = msg.get("usage", {})
        totals["input_tokens"] += usage.get("input", 0)
        totals["output_tokens"] += usage.get("output", 0)
        totals["cache_read_tokens"] += usage.get("cacheRead", 0)
        totals["cache_write_tokens"] += usage.get("cacheWrite", 0)
        totals["total_tokens"] += usage.get("totalTokens", 0)
        cost = usage.get("cost", {})
        totals["cost_usd"] += cost.get("total", 0.0)

    return totals


def _normalize_expected_model(model_id: str) -> tuple[Optional[str], str]:
    """Normalize configured model id into (provider, model) for comparison."""
    if "/" not in model_id:
        return None, model_id

    provider, model = model_id.split("/", 1)
    # Benchmarks pass OpenRouter models as "openrouter/<provider>/<model>".
    # Transcript assistant messages store model as "<provider>/<model>".
    if provider == "openrouter":
        return "openrouter", model
    return provider, model


def _detect_model_mismatch(
    transcript: List[Dict[str, Any]],
    expected_model_id: str,
) -> Optional[str]:
    """Return mismatch detail when successful assistant turns use a different model."""
    expected_provider, expected_model = _normalize_expected_model(expected_model_id)

    mismatches: List[str] = []
    for entry in transcript:
        if entry.get("type") != "message":
            continue
        msg = entry.get("message", {})
        if msg.get("role") != "assistant":
            continue
        if msg.get("stopReason") == "error":
            # Ignore failed model calls; they are useful for diagnostics but do
            # not represent the model that actually produced task output.
            continue

        actual_provider = msg.get("provider")
        actual_model = msg.get("model")
        if not actual_model:
            continue

        provider_mismatch = expected_provider is not None and actual_provider != expected_provider
        model_mismatch = actual_model != expected_model and actual_model != expected_model_id
        if provider_mismatch or model_mismatch:
            mismatches.append(f"{actual_provider or 'unknown'}/{actual_model}")

    if not mismatches:
        return None

    unique = sorted(set(mismatches))
    return (
        f"Model mismatch detected: expected {expected_model_id}, "
        f"but assistant output used {', '.join(unique)}"
    )


def execute_openclaw_task(
    *,
    task: Task,
    agent_id: str,
    model_id: str,
    run_id: str,
    timeout_multiplier: float,
    skill_dir: Path,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    logger.info("🤖 Agent [%s] starting task: %s", agent_id, task.task_id)
    logger.info("   Task: %s", task.name)
    logger.info("   Category: %s", task.category)
    if verbose:
        logger.info(
            "   Prompt: %s", task.prompt[:500] + "..." if len(task.prompt) > 500 else task.prompt
        )

    # Clean up previous session transcripts so we can reliably find this task's
    # transcript (OpenClaw uses its own UUID-based naming, not our session ID).
    cleanup_agent_sessions(agent_id)

    start_time = time.time()
    workspace = prepare_task_workspace(skill_dir, run_id, task, agent_id)
    session_id = f"{task.task_id}_{int(time.time() * 1000)}"
    timeout_seconds = task.timeout_seconds * timeout_multiplier
    stdout = ""
    stderr = ""
    exit_code = -1
    timed_out = False

    # Check if this is a multi-session task
    sessions = task.frontmatter.get("sessions", [])
    if sessions:
        # Multi-session task: send each prompt in sequence
        logger.info("📋 Multi-session task with %d sessions", len(sessions))
        for i, session_entry in enumerate(sessions, 1):
            # Extract prompt text from session entry (handle both string and dict formats)
            if isinstance(session_entry, str):
                session_prompt = session_entry
            elif isinstance(session_entry, dict):
                session_prompt = session_entry.get("prompt") or session_entry.get("message", "")
            else:
                logger.warning("⚠️ Skipping invalid session entry: %s", session_entry)
                continue

            logger.info("   Session %d/%d", i, len(sessions))
            elapsed = time.time() - start_time
            remaining = timeout_seconds - elapsed
            if remaining <= 0:
                timed_out = True
                break
            try:
                result = subprocess.run(
                    [
                        "openclaw",
                        "agent",
                        "--agent",
                        agent_id,
                        "--session-id",
                        session_id,
                        "--message",
                        session_prompt,
                    ],
                    capture_output=True,
                    text=True,
                    cwd=str(workspace),
                    timeout=remaining,
                    check=False,
            shell=USE_SHELL,
                )
                stdout += result.stdout
                stderr += result.stderr
                exit_code = result.returncode
                if result.returncode not in (0, -1):
                    break
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                stdout += _coerce_subprocess_output(exc.stdout)
                stderr += _coerce_subprocess_output(exc.stderr)
                break
            except FileNotFoundError as exc:
                stderr = f"openclaw command not found: {exc}"
                break
    else:
        # Single-session task: send task.prompt once
        try:
            result = subprocess.run(
                [
                    "openclaw",
                    "agent",
                    "--agent",
                    agent_id,
                    "--session-id",
                    session_id,
                    "--message",
                    task.prompt,
                ],
                capture_output=True,
                text=True,
                cwd=str(workspace),
                timeout=timeout_seconds,
                check=False,
            shell=USE_SHELL,
            )
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = _coerce_subprocess_output(exc.stdout)
            stderr = _coerce_subprocess_output(exc.stderr)
        except FileNotFoundError as exc:
            stderr = f"openclaw command not found: {exc}"

    transcript, transcript_path = _load_transcript(agent_id, session_id, start_time)
    usage = _extract_usage_from_transcript(transcript)
    execution_time = time.time() - start_time

    # Archive the raw transcript JSONL before cleanup_agent_sessions deletes it
    if transcript_path and output_dir:
        import shutil as _shutil
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_dest = output_dir / f"{task.task_id}.jsonl"
        try:
            _shutil.copy2(transcript_path, archive_dest)
            logger.info("Archived transcript to %s", archive_dest)
        except OSError as exc:
            logger.warning("Failed to archive transcript: %s", exc)

    status = "success"
    if timed_out:
        status = "timeout"
    if not transcript:
        status = "error"
    if exit_code not in (0, -1) and not timed_out:
        status = "error"
    if stderr and "openclaw command not found" in str(stderr):
        status = "error"
    model_mismatch = _detect_model_mismatch(transcript, model_id)
    if model_mismatch:
        status = "error"
        if stderr:
            stderr = f"{stderr.rstrip()}\n{model_mismatch}"
        else:
            stderr = model_mismatch

    # Use the effective agent workspace path in result payload so downstream
    # grading always evaluates where artifacts were actually written.
    effective_workspace = _get_agent_workspace(agent_id) or workspace
    if effective_workspace.resolve() != workspace.resolve():
        logger.warning(
            "Workspace mismatch detected (%s != %s); using effective workspace in result",
            workspace,
            effective_workspace,
        )

    # Verbose logging for debugging
    if verbose:
        logger.info("   [VERBOSE] Exit code: %s", exit_code)
        logger.info("   [VERBOSE] Execution time: %.2fs", execution_time)
        logger.info("   [VERBOSE] Workspace: %s", workspace)
        if stdout:
            logger.info("   [VERBOSE] Stdout (first 1000 chars):\n%s", stdout[:1000])
        if stderr:
            logger.info("   [VERBOSE] Stderr:\n%s", stderr[:1000])
        logger.info("   [VERBOSE] Transcript entries: %d", len(transcript))

        # Show agent responses from transcript
        for entry in transcript:
            if entry.get("type") == "message":
                msg = entry.get("message", {})
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if role == "assistant":
                    # Truncate long responses
                    preview = content[:500] + "..." if len(content) > 500 else content
                    logger.info("   [VERBOSE] Agent response: %s", preview)
                elif role == "user":
                    preview = content[:200] + "..." if len(content) > 200 else content
                    logger.info("   [VERBOSE] User message: %s", preview)

        # Show workspace files after task
        if effective_workspace.exists():
            logger.info("   [VERBOSE] Workspace files after task:")
            for f in sorted(effective_workspace.rglob("*")):
                if f.is_file():
                    try:
                        size = f.stat().st_size
                        logger.info("      %s (%d bytes)", f.relative_to(effective_workspace), size)
                    except OSError:
                        logger.info("      %s", f.relative_to(effective_workspace))

    return {
        "agent_id": agent_id,
        "task_id": task.task_id,
        "status": status,
        "transcript": transcript,
        "usage": usage,
        "workspace": str(effective_workspace),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "execution_time": execution_time,
        "stdout": stdout,
        "stderr": stderr,
    }


def run_openclaw_prompt(
    *,
    agent_id: str,
    prompt: str,
    workspace: Path,
    timeout_seconds: float,
) -> Dict[str, Any]:
    """Run a single OpenClaw prompt for helper agents like the judge."""
    cleanup_agent_sessions(agent_id)

    agent_workspace = _get_agent_workspace(agent_id)
    if agent_workspace and agent_workspace.exists():
        for bootstrap_file in ["BOOTSTRAP.md", "SOUL.md", "USER.md", "IDENTITY.md", "HEARTBEAT.md"]:
            bp = agent_workspace / bootstrap_file
            if bp.exists():
                try:
                    bp.unlink()
                    logger.debug("Removed bootstrap file from judge workspace: %s", bootstrap_file)
                except OSError as exc:
                    logger.warning("Failed to remove bootstrap file %s: %s", bootstrap_file, exc)

    start_time = time.time()
    workspace.mkdir(parents=True, exist_ok=True)
    session_id = f"judge_{int(time.time() * 1000)}"
    stdout = ""
    stderr = ""
    exit_code = -1
    timed_out = False

    chunks = [
        prompt[i : i + JUDGE_MAX_MSG_CHARS]
        for i in range(0, max(1, len(prompt)), JUDGE_MAX_MSG_CHARS)
    ]
    if len(chunks) > 1:
        total_chunks = len(chunks)
        chunks = [
            (
                f"You are receiving a long prompt in {total_chunks} parts.\n"
                f"Ignore and do not respond until the final part.\n\n"
                f"Part 1/{total_chunks}:\n{chunks[0]}"
            )
        ] + [
            (
                f"Part {i + 2}/{total_chunks}:\n{chunks[i + 1]}"
                if i + 2 < total_chunks
                else (
                    f"Part {i + 2}/{total_chunks} (final):\n{chunks[i + 1]}\n"
                    "All parts received. Proceed with final judgment now."
                )
            )
            for i in range(0, total_chunks - 1)
        ]
    for chunk in chunks:
        elapsed = time.time() - start_time
        remaining = timeout_seconds - elapsed
        if remaining <= 0:
            timed_out = True
            break
        try:
            openclaw_path = os.environ.get("OPENCLAW_PATH", "openclaw")
            # On Windows, cmd.exe splits command-line arguments at literal newlines,
            # causing the message to be truncated after the first line.
            # Escape newlines to literal \n sequences so the full prompt is received.
            send_chunk = (
                chunk.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
                if USE_SHELL
                else chunk
            )
            result = subprocess.run(
                [
                    openclaw_path,
                    "agent",
                    "--agent",
                    agent_id,
                    "--session-id",
                    session_id,
                    "--message",
                    send_chunk,
                ],
                capture_output=True,
                text=True,
                cwd=str(workspace),
                timeout=remaining,
                check=False,
                shell=USE_SHELL,
            )
            stdout += result.stdout
            stderr += result.stderr
            exit_code = result.returncode
            if result.returncode not in (0, -1) and not timed_out:
                break
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout += _coerce_subprocess_output(exc.stdout)
            stderr += _coerce_subprocess_output(exc.stderr)
            break
        except FileNotFoundError as exc:
            stderr += f"openclaw command not found: {exc}"
            break

    transcript, _ = _load_transcript(agent_id, session_id, start_time)
    execution_time = time.time() - start_time

    status = "success"
    if timed_out:
        status = "timeout"
    if not transcript:
        status = "error"
    if exit_code not in (0, -1) and not timed_out:
        status = "error"
    if stderr and "openclaw command not found" in str(stderr):
        status = "error"

    return {
        "agent_id": agent_id,
        "status": status,
        "transcript": transcript,
        "workspace": str(workspace),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "execution_time": execution_time,
        "stdout": stdout,
        "stderr": stderr,
    }


_JUDGE_SYSTEM_MSG = (
    "You are a strict grading function. "
    "Respond with ONLY a JSON object, no prose, no markdown fences, no extra text."
)


def call_judge_api(
    *,
    prompt: str,
    model: str,
    timeout_seconds: float = 120.0,
) -> Dict[str, Any]:
    """Call a judge model directly via API, bypassing OpenClaw.

    Dispatches based on model prefix:
      - openrouter/* -> OpenRouter chat completions API
      - anthropic/*  -> Anthropic Messages API
      - openai/*     -> OpenAI chat completions API
      - claude       -> headless Claude CLI (claude -p)

    Returns {"status": str, "text": str, "error"?: str}.
    """
    if model == "claude" or model.startswith("claude:"):
        return _judge_via_claude_cli(prompt, model, timeout_seconds)
    if model.startswith("anthropic/"):
        return _judge_via_anthropic(prompt, model, timeout_seconds)
    if model.startswith("openai/"):
        return _judge_via_openai(prompt, model, timeout_seconds)
    # Default: OpenRouter (handles openrouter/ prefix and bare provider/model)
    return _judge_via_openrouter(prompt, model, timeout_seconds)


def _judge_via_openai_compat(
    prompt: str,
    api_model: str,
    endpoint: str,
    api_key: str,
    timeout_seconds: float,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Shared implementation for OpenAI-compatible chat completions APIs."""
    payload = json.dumps({
        "model": api_model,
        "messages": [
            {"role": "system", "content": _JUDGE_SYSTEM_MSG},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_completion_tokens": 2048,
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    req = request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        logger.error("Judge API error (%s): %s", exc.code, body)
        return {"status": "error", "text": "", "error": f"HTTP {exc.code}: {body}"}
    except error.URLError as exc:
        logger.error("Judge network error: %s", exc)
        return {"status": "error", "text": "", "error": str(exc)}
    except TimeoutError:
        return {"status": "timeout", "text": "", "error": "Request timed out"}

    choices = data.get("choices", [])
    if not choices:
        return {"status": "error", "text": "", "error": "No choices in response"}
    text = choices[0].get("message", {}).get("content", "")
    return {"status": "success", "text": text}


def _judge_via_openrouter(prompt: str, model: str, timeout_seconds: float) -> Dict[str, Any]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return {"status": "error", "text": "", "error": "OPENROUTER_API_KEY not set"}
    bare_model = model.removeprefix("openrouter/")
    return _judge_via_openai_compat(
        prompt, bare_model,
        "https://openrouter.ai/api/v1/chat/completions",
        api_key, timeout_seconds,
        extra_headers={"HTTP-Referer": "https://pinchbench.com", "X-Title": "PinchBench-Judge"},
    )


def _judge_via_openai(prompt: str, model: str, timeout_seconds: float) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "text": "", "error": "OPENAI_API_KEY not set"}
    bare_model = model.removeprefix("openai/")
    return _judge_via_openai_compat(
        prompt, bare_model,
        "https://api.openai.com/v1/chat/completions",
        api_key, timeout_seconds,
    )


def _judge_via_anthropic(prompt: str, model: str, timeout_seconds: float) -> Dict[str, Any]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"status": "error", "text": "", "error": "ANTHROPIC_API_KEY not set"}
    bare_model = model.removeprefix("anthropic/")
    payload = json.dumps({
        "model": bare_model,
        "max_tokens": 2048,
        "temperature": 0.0,
        "system": _JUDGE_SYSTEM_MSG,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    req = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload, headers=headers, method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        logger.error("Anthropic judge API error (%s): %s", exc.code, body)
        return {"status": "error", "text": "", "error": f"HTTP {exc.code}: {body}"}
    except error.URLError as exc:
        logger.error("Anthropic judge network error: %s", exc)
        return {"status": "error", "text": "", "error": str(exc)}
    except TimeoutError:
        return {"status": "timeout", "text": "", "error": "Request timed out"}

    content = data.get("content", [])
    text = "".join(block.get("text", "") for block in content if block.get("type") == "text")
    return {"status": "success", "text": text}


def _judge_via_claude_cli(prompt: str, model: str, timeout_seconds: float) -> Dict[str, Any]:
    """Use headless Claude CLI (claude -p) as judge."""
    cmd: List[str] = ["claude", "-p"]
    # Support "claude:model-name" to pass --model
    if ":" in model:
        _, cli_model = model.split(":", 1)
        cmd.extend(["--model", cli_model])
    try:
        result = subprocess.run(
            cmd,
            input=f"{_JUDGE_SYSTEM_MSG}\n\n{prompt}",
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return {"status": "error", "text": "", "error": "claude CLI not found"}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "text": "", "error": "claude -p timed out"}
    if result.returncode != 0:
        return {"status": "error", "text": "", "error": f"claude exit {result.returncode}: {result.stderr[:300]}"}
    return {"status": "success", "text": result.stdout}
