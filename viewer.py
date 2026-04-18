#!/usr/bin/env python3
"""PinchBench Viewer — HTTP server + SPA for browsing run results and transcripts."""

import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http import cookies
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

SCRIPTS_DIR = Path(__file__).parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lib_agent import slugify_model
from lib_paths import RESULTS_ROOT, iter_summary_paths

RESULTS_DIR = Path(__file__).parent / "results"
SKILL_ROOT = Path(__file__).parent
TASKS_DIR = Path(__file__).parent / "tasks"
BENCHMARK_SCRIPT = Path(__file__).parent / "scripts" / "benchmark.py"
RERUN_TMP_ROOT = RESULTS_ROOT / "temp"
PORT = int(os.environ.get("PORT", 7788))
AUTH_USERNAME = os.environ.get("VIEWER_AUTH_USERNAME", "wuyixuan")
AUTH_PASSWORD = os.environ.get("VIEWER_AUTH_PASSWORD", "wuyixuan")
SESSION_COOKIE = os.environ.get("VIEWER_SESSION_COOKIE", "pinchbench_auth")
SESSION_TTL_SECONDS = int(os.environ.get("VIEWER_SESSION_TTL", str(60 * 60 * 24 * 7)))
SESSION_SECRET = os.environ.get("VIEWER_SESSION_SECRET", AUTH_PASSWORD + "::pinchbench")
RERUN_JOBS: dict[str, dict] = {}
RERUN_JOBS_LOCK = threading.Lock()
_LEGACY_RESULT_FILE_RE = re.compile(r"^\d{4}_.+\.json$")


def _looks_like_benchmark_result_json(path: Path) -> bool:
    if path.name == "summary.json":
        return True
    return bool(_LEGACY_RESULT_FILE_RE.match(path.name))


def _is_benchmark_result_payload(data: object) -> bool:
    if not isinstance(data, dict):
        return False
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        return False
    return bool(data.get("run_id") or data.get("model") or data.get("benchmark_version"))


def _iter_external_result_json_paths() -> list[Path]:
    """
    Discover benchmark result JSONs outside default results/ tree.
    This supports custom --output-dir runs that write NNNN_<model>.json.
    """
    paths: list[Path] = []
    for path in sorted(SKILL_ROOT.rglob("*.json")):
        if not path.is_file():
            continue
        if ".viewer_backups" in path.parts:
            continue
        # Keep default tree handled by existing logic.
        try:
            path.resolve().relative_to(RESULTS_DIR.resolve())
            continue
        except ValueError:
            pass
        if not _looks_like_benchmark_result_json(path):
            continue
        paths.append(path)
    return paths


def _sign_session(username: str, expires: int) -> str:
    msg = f"{username}:{expires}".encode("utf-8")
    return hmac.new(SESSION_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def _make_session_token(username: str) -> str:
    expires = int(time.time()) + SESSION_TTL_SECONDS
    sig = _sign_session(username, expires)
    return f"{username}:{expires}:{sig}"


def _verify_session_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        username, expires_s, sig = token.split(":", 2)
        expires = int(expires_s)
    except Exception:
        return False
    if username != AUTH_USERNAME:
        return False
    if expires < int(time.time()):
        return False
    expected = _sign_session(username, expires)
    return hmac.compare_digest(sig, expected)

# 用户消息常见前缀：[Sun 2026-04-12 13:26 UTC] 正文…
_USER_BRACKET_PREFIX = re.compile(r"^\s*\[([^\]]+)\]\s*", re.UNICODE)


def _split_user_bracket_prefix(text: str | None) -> tuple[str | None, str]:
    """剥离开头的方括号时间戳，返回 (括号内原文, 剩余正文)。"""
    if not text:
        return None, ""
    t = text.lstrip("\ufeff")
    m = _USER_BRACKET_PREFIX.match(t)
    if not m:
        return None, t
    return m.group(1), t[m.end() :]


def _iter_result_summary_paths() -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for path in sorted(RESULTS_DIR.glob("*.json")):
        if path not in seen:
            paths.append(path)
            seen.add(path)
    for path in iter_summary_paths():
        if ".viewer_backups" in path.parts:
            continue
        if path not in seen:
            paths.append(path)
            seen.add(path)
    for path in _iter_external_result_json_paths():
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def _display_path_for_result(path: Path) -> str:
    """Short path for UI, e.g. formal/<model_slug>/foundation."""
    try:
        rel = path.resolve().relative_to(RESULTS_DIR.resolve())
        parts = rel.parts
        if (
            parts
            and parts[0] in ("formal", "temp")
            and parts[-1] == "summary.json"
            and len(parts) >= 2
        ):
            if len(parts) >= 4:
                return f"{parts[0]}/{parts[1]}/{parts[2]}"
            return f"{parts[0]}/{parts[1]}"
    except ValueError:
        pass
    return path.name


def _result_key_from_path(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(RESULTS_DIR.resolve())
        parts = rel.parts
        if len(parts) >= 4 and parts[0] in ("formal", "temp") and parts[-1] == "summary.json":
            return parts[2]
        if len(parts) >= 3 and parts[0] in ("formal", "temp") and parts[-1] == "summary.json":
            return "all"
    except ValueError:
        pass
    return "all"


def _run_identity(model_slug: str, result_key: str) -> str:
    return f"{model_slug}__{result_key}"


def _result_json_path_for_run(run_id: str) -> Path | None:
    rid = (run_id or "").strip()
    if not rid:
        return None
    if "__" in rid:
        model_slug, result_key = rid.rsplit("__", 1)
        for scope in ("formal", "temp"):
            candidate = RESULTS_DIR / scope / model_slug / result_key / "summary.json"
            if candidate.is_file():
                return candidate
            if result_key == "all":
                legacy_candidate = RESULTS_DIR / scope / model_slug / "summary.json"
                if legacy_candidate.is_file():
                    return legacy_candidate
    # Old layout: results/<scope>/<model_slug>/summary.json when run_id is model slug
    for scope in ("formal", "temp"):
        candidate = RESULTS_DIR / scope / rid / "summary.json"
        if candidate.is_file():
            return candidate
    # Legacy flat file: NNNN_modelslug.json
    for path in sorted(RESULTS_DIR.glob(f"{rid}_*.json")):
        if path.is_file():
            return path
    # Match by run_id / legacy_run_id inside discovered result JSON payloads
    for path in _iter_result_summary_paths():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not _is_benchmark_result_payload(data):
            continue
        if data.get("run_id") == rid or str(data.get("legacy_run_id", "")) == rid:
            return path
    # Match by model slug (legacy viewer behavior)
    by_model: list[tuple[float, Path]] = []
    for path in _iter_result_summary_paths():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not _is_benchmark_result_payload(data):
            continue
        model = data.get("model")
        if isinstance(model, str) and slugify_model(model) == rid:
            by_model.append((float(data.get("timestamp") or 0.0), path))
    if by_model:
        by_model.sort(key=lambda item: item[0], reverse=True)
        return by_model[0][1]
    # Old nested layout: results/<scope>/<model>/<digits>/summary.json
    if rid.isdigit():
        for scope in ("formal", "temp"):
            root = RESULTS_DIR / scope
            if not root.is_dir():
                continue
            for summary_path in root.rglob("summary.json"):
                if summary_path.parent.name == rid:
                    return summary_path
    return None


def _transcript_dir_for_run(run_id: str) -> Path | None:
    target_json = _result_json_path_for_run(run_id)
    if target_json is None:
        return None
    if target_json.name == "summary.json":
        transcripts_dir = target_json.parent / "transcripts"
        return transcripts_dir if transcripts_dir.is_dir() else None
    legacy_run_id = ""
    try:
        payload = json.loads(target_json.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            legacy_run_id = str(payload.get("run_id") or "").strip()
    except Exception:
        legacy_run_id = ""

    if not legacy_run_id:
        legacy_run_id = target_json.stem.split("_", 1)[0]

    sibling = target_json.parent / f"{legacy_run_id}_transcripts"
    if sibling.is_dir():
        return sibling

    direct = RESULTS_DIR / f"{legacy_run_id}_transcripts"
    return direct if direct.is_dir() else None


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def get_runs():
    """Return latest run summaries keyed by model + result selection."""
    runs_by_model: dict[tuple[str, str], dict] = {}
    for p in _iter_result_summary_paths():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not _is_benchmark_result_payload(data):
            continue
        tasks = data.get("tasks", [])
        scored = [t for t in tasks if t.get("grading")]
        total_score = sum(t["grading"]["mean"] for t in scored if t["grading"].get("mean") is not None)
        max_score = len(scored)
        model = data.get("model", "unknown")
        model_slug = slugify_model(model) if isinstance(model, str) and model else str(data.get("run_id", p.stem))
        result_key = str(data.get("result_key") or _result_key_from_path(p) or "all")
        run_identity = _run_identity(model_slug, result_key)
        item = {
            "run_id": run_identity,
            "model_slug": model_slug,
            "result_key": result_key,
            "legacy_run_id": data.get("run_id", p.stem),
            "display_path": _display_path_for_result(p),
            "model": model,
            "timestamp": data.get("timestamp"),
            "benchmark_version": data.get("benchmark_version"),
            "task_count": len(tasks),
            "total_score": round(total_score, 3),
            "max_score": max_score,
            "file": str(p),
        }
        group_key = (model_slug, result_key)
        prev = runs_by_model.get(group_key)
        if prev is None or float(item.get("timestamp") or 0.0) >= float(prev.get("timestamp") or 0.0):
            runs_by_model[group_key] = item
    runs = list(runs_by_model.values())
    runs.sort(key=lambda r: r.get("timestamp") or 0, reverse=True)
    return runs


def get_run_detail(run_id: str):
    """Return full run detail from legacy or structured result paths."""
    p = _result_json_path_for_run(run_id)
    if p is None:
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not _is_benchmark_result_payload(data):
        return None
    model = data.get("model")
    result_key = str(data.get("result_key") or _result_key_from_path(p) or "all")
    data["model_slug"] = slugify_model(model) if isinstance(model, str) and model else str(run_id)
    data["result_key"] = result_key
    data["legacy_run_id"] = data.get("run_id")
    data["run_id"] = _run_identity(data["model_slug"], result_key)
    data["viewer_display_path"] = _display_path_for_result(p)
    return data


def get_leaderboard():
    """Return model leaderboard by score/speed/cost from latest summary per model."""
    rows: list[dict] = []
    for run in get_runs():
        run_id = str(run.get("run_id") or "")
        detail = get_run_detail(run_id)
        if not detail:
            continue

        tasks = detail.get("tasks") or []
        scored = [t for t in tasks if isinstance(t, dict) and t.get("grading")]
        total_score = sum(float((t.get("grading") or {}).get("mean") or 0.0) for t in scored)
        max_score = len(scored)
        score_pct = (total_score / max_score * 100.0) if max_score else 0.0
        success_task_count = sum(1 for t in tasks if (t or {}).get("status") == "success")

        efficiency = detail.get("efficiency") or {}
        total_execution_seconds = float(
            efficiency.get("total_execution_time_seconds")
            or sum(float((t or {}).get("execution_time") or 0.0) for t in tasks)
        )
        total_cost_usd = float(
            efficiency.get("total_cost_usd")
            or sum(float(((t or {}).get("usage") or {}).get("cost_usd") or 0.0) for t in tasks)
        )

        task_count = len(tasks)
        avg_task_seconds = (total_execution_seconds / task_count) if task_count else 0.0
        avg_cost_per_task_usd = (total_cost_usd / task_count) if task_count else 0.0

        rows.append(
            {
                "run_id": run_id,
                "model_slug": detail.get("model_slug") or run_id,
                "result_key": detail.get("result_key") or "all",
                "model": detail.get("model") or "unknown",
                "display_path": detail.get("viewer_display_path") or run.get("display_path") or "",
                "timestamp": detail.get("timestamp") or run.get("timestamp"),
                "task_count": task_count,
                "success_task_count": success_task_count,
                "total_score": round(total_score, 3),
                "max_score": max_score,
                "score_pct": round(score_pct, 2),
                "total_execution_seconds": round(total_execution_seconds, 2),
                "avg_task_seconds": round(avg_task_seconds, 2),
                "total_cost_usd": round(total_cost_usd, 6),
                "avg_cost_per_task_usd": round(avg_cost_per_task_usd, 6),
            }
        )

    rows.sort(
        key=lambda r: (
            -float(r.get("score_pct") or 0.0),
            float(r.get("avg_task_seconds") or 0.0),
            float(r.get("total_cost_usd") or 0.0),
            -float(r.get("timestamp") or 0.0),
        )
    )
    return rows


def _compute_efficiency_summary(task_entries: list[dict]) -> dict:
    total_tokens = sum(int((t.get("usage") or {}).get("total_tokens") or 0) for t in task_entries)
    total_input_tokens = sum(int((t.get("usage") or {}).get("input_tokens") or 0) for t in task_entries)
    total_output_tokens = sum(int((t.get("usage") or {}).get("output_tokens") or 0) for t in task_entries)
    total_cost_usd = sum(float((t.get("usage") or {}).get("cost_usd") or 0.0) for t in task_entries)
    total_requests = sum(int((t.get("usage") or {}).get("request_count") or 0) for t in task_entries)
    total_execution_time_seconds = sum(float(t.get("execution_time") or 0.0) for t in task_entries)
    tasks_with_usage_data = sum(1 for t in task_entries if t.get("usage"))
    scores = [float((t.get("grading") or {}).get("mean") or 0.0) for t in task_entries]
    total_score = sum(scores)
    per_task = []
    for task in task_entries:
        usage = task.get("usage") or {}
        score = float((task.get("grading") or {}).get("mean") or 0.0)
        task_tokens = int(usage.get("total_tokens") or 0)
        task_cost = float(usage.get("cost_usd") or 0.0)
        per_task.append(
            {
                "task_id": task.get("task_id"),
                "score": round(score, 4),
                "total_tokens": task_tokens,
                "cost_usd": round(task_cost, 6),
                "tokens_per_score_point": round(task_tokens / score, 1) if score > 0 else None,
            }
        )
    task_count = len(task_entries)
    return {
        "total_tokens": total_tokens,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "total_requests": total_requests,
        "total_execution_time_seconds": round(total_execution_time_seconds, 2),
        "tasks_with_usage_data": tasks_with_usage_data,
        "tokens_per_task": round(total_tokens / task_count, 1) if task_count else 0.0,
        "cost_per_task_usd": round(total_cost_usd / task_count, 6) if task_count else 0.0,
        "score_per_1k_tokens": round(total_score / (total_tokens / 1000), 5) if total_tokens else 0.0,
        "score_per_dollar": round(total_score / total_cost_usd, 4) if total_cost_usd else 0.0,
        "per_task": per_task,
    }


def _backup_path_for(run_id: str, original_path: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    if original_path.name == "summary.json":
        backup_root = original_path.parent / ".viewer_backups"
    else:
        backup_root = RESULTS_DIR / ".viewer_backups"
    backup_dir = backup_root / run_id / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir / original_path.name


def _merge_rerun_result_into_run(run_id: str, task_id: str, rerun_json_path: Path) -> dict:
    target_json_path = _result_json_path_for_run(run_id)
    if target_json_path is None:
        raise FileNotFoundError(f"run result not found: {run_id}")
    rerun_data = json.loads(rerun_json_path.read_text(encoding="utf-8"))
    rerun_tasks = rerun_data.get("tasks") or []
    if len(rerun_tasks) != 1:
        raise ValueError(f"expected exactly 1 rerun task, got {len(rerun_tasks)}")
    rerun_task = rerun_tasks[0]
    rerun_run_id = rerun_data.get("run_id")
    if not rerun_run_id:
        raise ValueError("rerun result missing run_id")

    target_data = json.loads(target_json_path.read_text(encoding="utf-8"))
    target_tasks = target_data.get("tasks") or []
    task_index = next((i for i, t in enumerate(target_tasks) if t.get("task_id") == task_id), None)
    if task_index is None:
        raise ValueError(f"task not found in target run: {task_id}")

    json_backup = _backup_path_for(run_id, target_json_path)
    shutil.copy2(target_json_path, json_backup)

    if rerun_json_path.name == "summary.json":
        rerun_transcript_dir = rerun_json_path.parent / "transcripts"
    else:
        rerun_transcript_dir = rerun_json_path.parent / f"{rerun_run_id}_transcripts"
    rerun_transcript_path = rerun_transcript_dir / f"{task_id}.jsonl"
    if target_json_path.name == "summary.json":
        target_transcript_dir = target_json_path.parent / "transcripts"
    else:
        target_transcript_dir = RESULTS_DIR / f"{run_id}_transcripts"
    target_transcript_dir.mkdir(parents=True, exist_ok=True)
    target_transcript_path = target_transcript_dir / f"{task_id}.jsonl"
    transcript_backup = None
    if target_transcript_path.exists():
        transcript_backup = _backup_path_for(run_id, target_transcript_path)
        shutil.copy2(target_transcript_path, transcript_backup)
    if rerun_transcript_path.exists():
        shutil.copy2(rerun_transcript_path, target_transcript_path)

    if rerun_task.get("status") == "success":
        rerun_task["timed_out"] = False
    target_tasks[task_index] = rerun_task
    target_data["tasks"] = target_tasks
    target_data["efficiency"] = _compute_efficiency_summary(target_tasks)
    target_data["viewer_last_updated"] = time.time()
    target_json_path.write_text(
        json.dumps(target_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "target_json_path": str(target_json_path),
        "json_backup_path": str(json_backup),
        "target_transcript_path": str(target_transcript_path) if rerun_transcript_path.exists() else None,
        "transcript_backup_path": str(transcript_backup) if transcript_backup else None,
    }


def _set_rerun_job(job_id: str, **updates) -> dict:
    with RERUN_JOBS_LOCK:
        job = RERUN_JOBS.setdefault(job_id, {"job_id": job_id})
        job.update(updates)
        return dict(job)


def get_rerun_job(job_id: str) -> dict | None:
    with RERUN_JOBS_LOCK:
        job = RERUN_JOBS.get(job_id)
        return dict(job) if job else None


def _run_task_rerun_worker(job_id: str, run_id: str, task_id: str, model: str) -> None:
    tmp_dir = RERUN_TMP_ROOT / slugify_model(model) / job_id
    _set_rerun_job(job_id, status="running", started_at=time.time(), tmp_dir=str(tmp_dir))
    try:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            sys.executable,
            str(BENCHMARK_SCRIPT),
            "--model",
            model,
            "--suite",
            task_id,
            "--output-dir",
            str(tmp_dir),
            "--no-fail-fast",
            "--timeout-multiplier",
            "2",
        ]
        env = os.environ.copy()
        env["PINCHBENCH_RUN_SCOPE"] = "temp"
        # 30-minute hard cap: single-task execute+grade should never need more.
        # Without this, a hung task leaves the worker thread blocked forever and
        # the UI shows "运行中..." indefinitely.
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(Path(__file__).parent),
                capture_output=True,
                text=True,
                check=False,
                env=env,
                timeout=1800,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"rerun timed out after 30 minutes (task may need a higher --timeout-multiplier)"
            ) from exc
        result_files = sorted(tmp_dir.glob("*.json"))
        if not result_files:
            summary_path = tmp_dir / "summary.json"
            if summary_path.exists():
                result_files = [summary_path]
        if proc.returncode != 0 or not result_files:
            raise RuntimeError(
                "rerun failed"
                + (f" (exit {proc.returncode})" if proc.returncode != 0 else "")
                + (f": {proc.stderr[-500:]}" if proc.stderr else "")
            )
        merged = _merge_rerun_result_into_run(run_id, task_id, result_files[0])
        _set_rerun_job(
            job_id,
            status="completed",
            finished_at=time.time(),
            return_code=proc.returncode,
            merged=merged,
            stdout_tail=proc.stdout[-2000:],
            stderr_tail=proc.stderr[-2000:],
        )
    except Exception as exc:
        _set_rerun_job(
            job_id,
            status="failed",
            finished_at=time.time(),
            error=str(exc),
        )


def start_task_rerun(run_id: str, task_id: str) -> dict:
    run_data = get_run_detail(run_id)
    if run_data is None:
        raise FileNotFoundError(f"run not found: {run_id}")
    task_entry = next((t for t in (run_data.get("tasks") or []) if t.get("task_id") == task_id), None)
    if task_entry is None:
        raise FileNotFoundError(f"task not found in run: {task_id}")
    model = run_data.get("model")
    if not model:
        raise ValueError("run missing model")

    job_id = f"{run_id}-{task_id}-{int(time.time() * 1000)}"
    _set_rerun_job(
        job_id,
        status="queued",
        run_id=run_id,
        task_id=task_id,
        model=model,
        created_at=time.time(),
    )
    worker = threading.Thread(
        target=_run_task_rerun_worker,
        args=(job_id, run_id, task_id, model),
        daemon=True,
    )
    worker.start()
    return get_rerun_job(job_id) or {"job_id": job_id, "status": "queued"}


def get_transcript(run_id: str, task_id: str):
    """Parse a .jsonl transcript into a structured conversation."""
    transcript_dir = _transcript_dir_for_run(run_id)
    if transcript_dir is None:
        return None
    path = transcript_dir / f"{task_id}.jsonl"
    if not path.exists():
        return None

    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            pass

    # Build conversation turns from message events
    turns = []
    meta = {}
    for ev in events:
        t = ev.get("type")
        if t == "session":
            meta["session_id"] = ev.get("id")
            meta["cwd"] = ev.get("cwd")
        elif t == "model_change":
            meta["provider"] = ev.get("provider")
            meta["model_id"] = ev.get("modelId")
        elif t == "message":
            msg = ev.get("message", {})
            role = msg.get("role")
            contents = msg.get("content", [])
            turn = {
                "role": role,
                "timestamp": ev.get("timestamp"),
                "parts": [],
            }
            if role == "toolResult":
                turn["tool_call_id"] = msg.get("toolCallId")
                turn["tool_name"] = msg.get("toolName")

            for c in contents:
                ct = c.get("type")
                if ct == "text":
                    turn["parts"].append({"type": "text", "text": c.get("text", "")})
                elif ct == "thinking":
                    turn["parts"].append({"type": "thinking", "text": c.get("thinking", "")})
                elif ct == "toolCall":
                    turn["parts"].append({
                        "type": "toolCall",
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "arguments": c.get("arguments", {}),
                    })
            if role == "user":
                full_text = "".join(
                    p.get("text", "") for p in turn["parts"] if p.get("type") == "text"
                )
                bracket, body_only = _split_user_bracket_prefix(full_text)
                turn["user_time_bracket"] = bracket
                turn["user_body_text"] = body_only
                mt = msg.get("timestamp")
                if isinstance(mt, (int, float)):
                    turn["timestamp_ms"] = int(mt)
            turns.append(turn)

    return {"meta": meta, "turns": turns}


def get_task_description(task_id: str):
    """Return raw markdown for a task definition."""
    path = TASKS_DIR / f"{task_id}.md"
    if path.exists():
        return path.read_text()
    return None


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

LOGIN_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PinchBench Viewer Login</title>
<style>
  :root {
    --bg: #f3f4f6;
    --card: #ffffff;
    --border: #e5e7eb;
    --text: #111827;
    --muted: #6b7280;
    --accent: #c75c5c;
    --accent-dark: #a84848;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at top, #fff7f7 0%, var(--bg) 48%, #eceff3 100%);
    font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--text);
  }
  .login-card {
    width: min(92vw, 420px);
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.08);
  }
  .brand {
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent);
    font-weight: 700;
    margin-bottom: 10px;
  }
  h1 {
    margin: 0 0 8px;
    font-size: 1.5rem;
    line-height: 1.2;
  }
  p.desc {
    margin: 0 0 22px;
    color: var(--muted);
    line-height: 1.6;
    font-size: 0.95rem;
  }
  label {
    display: block;
    margin-bottom: 14px;
    font-size: 0.85rem;
    font-weight: 600;
  }
  input {
    width: 100%;
    margin-top: 8px;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }
  input:focus {
    border-color: rgba(199,92,92,0.65);
    box-shadow: 0 0 0 4px rgba(199,92,92,0.12);
  }
  button {
    width: 100%;
    border: none;
    border-radius: 12px;
    background: var(--accent);
    color: #fff;
    padding: 12px 14px;
    font-size: 0.95rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.15s, transform 0.05s;
  }
  button:hover { background: var(--accent-dark); }
  button:active { transform: translateY(1px); }
  .error {
    margin-bottom: 14px;
    padding: 10px 12px;
    border-radius: 12px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #b91c1c;
    font-size: 0.88rem;
  }
  .hint {
    margin-top: 14px;
    font-size: 0.8rem;
    color: var(--muted);
    text-align: center;
  }
</style>
</head>
<body>
  <form class="login-card" method="POST" action="/login">
    <div class="brand">PinchBench</div>
    <h1>受保护页面</h1>
    <p class="desc">请输入账号和密码。只有指定用户才可以访问 7788 这个页面。</p>
    __ERROR__
    <label>
      用户名
      <input type="text" name="username" autocomplete="username" placeholder="请输入用户名" required />
    </label>
    <label>
      密码
      <input type="password" name="password" autocomplete="current-password" placeholder="请输入密码" required />
    </label>
    <button type="submit">登录</button>
    <div class="hint">登录成功后会写入会话 Cookie</div>
  </form>
</body>
</html>
"""

HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PinchBench Viewer</title>
<script src="/assets/marked.min.js" defer></script>
<link rel="stylesheet" href="/assets/github-dark.min.css">
<script src="/assets/highlight.min.js" defer></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #f0f1f4;
    --surface: #ffffff;
    --surface2: #f4f5f7;
    --border: #e4e7ee;
    --accent: #c75c5c;
    --accent2: #b84a4a;
    --green: #15803d;
    --yellow: #a16207;
    --red: #c53737;
    --text: #1a1d24;
    --muted: #6b7280;
    --thinking-bg: #fafbfc;
    --tool-bg: #fafbfc;
    --result-bg: #fafbfc;
    --radius: 12px;
    --radius-lg: 18px;
    --font: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
    --mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
    /* OpenClaw chat (transcript) — 参考浅色 + 珊瑚红强调 */
    --oc-bg: #f5f5f6;
    --oc-coral: #c75c5c;
    --oc-coral-soft: rgba(199, 92, 92, 0.12);
    --oc-user-bubble: #fce8e8;
    --oc-user-border: rgba(199, 92, 92, 0.2);
    --oc-chip-bg: #ffffff;
    --oc-chip-border: #e8e9ec;
    --oc-bolt: #c75c5c;
    --oc-final-bg: #ffffff;
    --oc-final-border: rgba(0,0,0,0.06);
    --oc-nav-border: rgba(0,0,0,0.06);
    --oc-pill-bg: #fafafa;
    --md-inline-bg: #eceef2;
    --md-pre-bg: #1e293b;
  }

  body.theme-dark {
    --bg: #0f1115;
    --surface: #171a21;
    --surface2: #1c2028;
    --border: #2a2f3a;
    --text: #e8eaed;
    --muted: #9aa0a8;
    --oc-bg: #14161c;
    --oc-chip-bg: #1a1d24;
    --oc-chip-border: #2f3542;
    --oc-user-bubble: #2a1f22;
    --oc-user-border: rgba(199, 92, 92, 0.35);
    --oc-final-bg: #171a21;
    --oc-pill-bg: #1c2028;
    --md-inline-bg: #2a303c;
    --thinking-bg: #1a1d24;
    --tool-bg: #1a1d24;
    --result-bg: #1a1d24;
  }

  body { font-family: var(--font); background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }

  /* ── Layout ── */
  #app { display: flex; flex: 1; overflow: hidden; min-height: 0; }
  #sidebar { width: 260px; min-width: 200px; border-right: 1px solid var(--border); background: var(--surface); display: flex; flex-direction: column; overflow: hidden; min-height: 0; }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-height: 0; background: var(--bg); }
  #task-panel { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 22px; }
  #detail-pane { display: none; flex: 1; min-height: 0; flex-direction: column; overflow: hidden; }
  #detail-pane.open { display: flex; }

  /* ── OpenClaw 风格顶栏 ── */
  #oc-header { flex-shrink: 0; background: var(--surface); border-bottom: 1px solid var(--oc-nav-border); z-index: 20; }
  .oc-nav-top {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 20px; gap: 16px; flex-wrap: wrap;
  }
  .oc-nav-left { display: flex; align-items: center; gap: 10px; min-width: 0; flex: 1; }
  #back-btn {
    display: none; flex-shrink: 0;
    cursor: pointer; background: var(--surface2); border: 1px solid var(--border);
    color: var(--text); width: 36px; height: 36px; border-radius: 12px;
    font-size: 1rem; line-height: 1; align-items: center; justify-content: center;
  }
  #back-btn:hover { background: var(--border); }
  .oc-crumb-main {
    font-size: 0.92rem; font-weight: 600; color: var(--text);
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap; min-width: 0;
  }
  .oc-crumb-main .oc-brand { color: var(--oc-coral); font-weight: 700; }
  .oc-crumb-main .oc-sep { color: var(--muted); font-weight: 500; opacity: 0.85; }
  .oc-crumb-main .oc-page { color: var(--muted); font-weight: 600; }

  .oc-nav-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .oc-search-pill {
    display: flex; align-items: center; gap: 10px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 999px; padding: 8px 14px; min-width: 160px; max-width: 240px;
    font-size: 0.8rem; color: var(--muted); cursor: default;
  }
  .oc-search-pill .oc-kbd {
    font-size: 0.68rem; font-family: var(--mono);
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 2px 6px; color: var(--muted);
  }
  .oc-ico {
    width: 38px; height: 38px; border-radius: 12px;
    border: 1px solid var(--border); background: var(--surface);
    color: var(--muted); cursor: pointer; display: inline-flex;
    align-items: center; justify-content: center; font-size: 1rem;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
  }
  .oc-ico:hover { color: var(--oc-coral); border-color: rgba(199, 92, 92, 0.45); background: var(--oc-coral-soft); }

  /* 子栏：三枚信息块 + 右侧操作 */
  .oc-subbar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 12px; padding: 10px 20px 14px; flex-wrap: wrap;
    border-top: 1px solid var(--oc-nav-border);
  }
  .oc-subbar.is-hidden { display: none; }
  .oc-subbar-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; min-width: 0; flex: 1; }
  .oc-pill {
    display: inline-flex; align-items: center; max-width: 100%;
    background: var(--oc-pill-bg); border: 1px solid var(--border);
    border-radius: 14px; padding: 8px 14px; font-size: 0.78rem;
    color: var(--text); line-height: 1.35;
    box-shadow: 0 1px 0 rgba(0,0,0,0.02);
  }
  .oc-pill .oc-pill-muted { color: var(--muted); font-weight: 500; margin-right: 4px; }
  .oc-pill code, .oc-pill .mono { font-family: var(--mono); font-size: 0.74rem; word-break: break-all; }

  .oc-subbar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
  .oc-ico-sm {
    width: 36px; height: 36px; border-radius: 11px;
    border: 1px solid var(--border); background: var(--surface);
    color: var(--muted); cursor: pointer; display: inline-flex;
    align-items: center; justify-content: center; font-size: 0.95rem;
    transition: color 0.15s, border-color 0.15s, background 0.15s;
  }
  .oc-ico-sm:hover { color: var(--oc-coral); border-color: rgba(199, 92, 92, 0.4); }
  .oc-ico-sm.oc-accent {
    border-color: rgba(199, 92, 92, 0.55); color: var(--oc-coral);
    background: rgba(255,255,255,0.6);
  }
  body.theme-dark .oc-ico-sm.oc-accent { background: rgba(199, 92, 92, 0.12); }
  .oc-vsep { width: 1px; height: 22px; background: var(--border); margin: 0 4px; }

  /* ── Sidebar runs ── */
  #sidebar-header {
    padding: 10px 12px 8px;
    flex-shrink: 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }
  #sidebar-header .sidebar-title {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .sidebar-btn {
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--text);
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 0.72rem;
    cursor: pointer;
    line-height: 1;
  }
  .sidebar-btn:hover { border-color: var(--oc-coral); color: var(--oc-coral); background: var(--surface); }
  #run-list { overflow-y: auto; flex: 1; }
  .run-item { padding: 11px 14px; cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.15s; }
  .run-item:hover { background: var(--surface2); }
  .run-item.active { background: var(--oc-coral-soft); border-left: 3px solid var(--oc-coral); }
  .run-item .run-id { font-size: 0.78rem; font-weight: 700; color: var(--oc-coral); font-family: var(--mono); }
  .run-item .run-model { font-size: 0.78rem; color: var(--text); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .run-item .run-score { font-size: 0.72rem; color: var(--muted); margin-top: 4px; }

  /* ── Task grid ── */
  .section-title { font-size: 0.8rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 14px; }
  .run-summary-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
  .run-summary-head .section-title { margin-bottom: 0; }
  #run-summary { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; margin-bottom: 20px; display: flex; gap: 32px; flex-wrap: wrap; }
  .stat { display: flex; flex-direction: column; gap: 2px; }
  .stat-val { font-size: 1.4rem; font-weight: 700; }
  .stat-label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

  #task-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 12px; }
  .task-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; cursor: pointer; transition: border-color 0.15s, transform 0.1s; }
  .task-card:hover { border-color: rgba(199, 92, 92, 0.45); transform: translateY(-1px); box-shadow: 0 4px 14px rgba(199, 92, 92, 0.08); }
  .task-card .tc-id { font-family: var(--mono); font-size: 0.72rem; color: var(--muted); }
  .task-card .tc-name { font-size: 0.88rem; font-weight: 600; margin: 4px 0 8px; }
  .task-card .tc-score { font-size: 1.1rem; font-weight: 700; }
  .task-card .tc-meta { font-size: 0.72rem; color: var(--muted); margin-top: 6px; display: flex; gap: 10px; }
  .task-card .tc-badge { display: inline-block; font-size: 0.68rem; padding: 2px 7px; border-radius: 999px; font-weight: 600; }
  .task-card .tc-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
  .action-btn { border: 1px solid var(--border); background: var(--surface2); color: var(--text); border-radius: 8px; padding: 5px 10px; font-size: 0.72rem; cursor: pointer; }
  .action-btn:hover:not(:disabled) { border-color: var(--oc-coral); color: var(--oc-coral); background: var(--surface); }
  .action-btn:disabled { opacity: 0.55; cursor: progress; }
  .action-btn.is-primary { background: var(--oc-coral-soft); color: var(--oc-coral); border-color: #efc9c9; }
  .badge-success { background: #dcfce7; color: var(--green); }
  .badge-timeout { background: #fee2e2; color: var(--red); }
  .badge-lowscore { background: #fef9c3; color: var(--yellow); }
  .badge-error { background: #fce7f3; color: #a21caf; }
  body.theme-dark .badge-success { background: #14532d; color: #86efac; }
  body.theme-dark .badge-timeout { background: #450a0a; color: #fca5a5; }
  body.theme-dark .badge-lowscore { background: #451a03; color: #fde047; }
  body.theme-dark .badge-error { background: #3b0764; color: #e9d5ff; }
  .score-high { color: var(--green); }
  .score-mid { color: var(--yellow); }
  .score-low { color: var(--red); }

  /* ── Detail pane（任务标题条，与顶栏子栏衔接） ── */
  #detail-header {
    padding: 12px 20px 14px; border-bottom: 1px solid var(--border);
    background: var(--surface); flex-shrink: 0;
  }
  #detail-header .dh-crumb { display: none; }
  #detail-header .dh-id { font-family: var(--mono); font-size: 0.72rem; color: var(--muted); margin-bottom: 4px; }
  #detail-header .dh-name { font-size: 1.02rem; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.02em; }
  #detail-header .dh-stats { display: flex; gap: 16px 22px; flex-wrap: wrap; }
  .dh-stat { font-size: 0.76rem; color: var(--muted); }
  .dh-stat span { color: var(--text); font-weight: 600; }

  #detail-body { display: flex; flex: 1; overflow: hidden; min-height: 0; position: relative; }
  #transcript-wrap { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
  #transcript-pane { flex: 1; overflow-y: auto; padding: 16px 18px 8px; display: flex; flex-direction: column; gap: 0; min-height: 0; overscroll-behavior: contain; background: var(--oc-bg); }

  /* 聊天区底部：本次输出文件（紧凑横排） */
  .transcript-artifacts {
    flex-shrink: 0; border-top: 1px solid var(--border); background: var(--surface);
    padding: 5px 10px 6px; display: flex; flex-direction: row; flex-wrap: wrap;
    align-items: center; gap: 6px 10px;
  }
  .transcript-artifacts.is-empty { display: none !important; }
  .ta-head {
    flex: 0 0 auto; width: auto; margin: 0;
    font-size: 0.65rem; font-weight: 700; color: var(--muted);
    text-transform: uppercase; letter-spacing: 0.05em; line-height: 1.2;
  }
  .ta-strip {
    flex: 1 1 auto; min-width: 0; display: flex; flex-wrap: wrap;
    gap: 6px; align-items: center; overflow-x: auto; padding: 2px 0;
  }
  /* 扁平长方形条：左图标 + 文案，无缩略图 */
  .ta-card {
    flex: 0 1 auto; min-width: 120px; max-width: min(100%, 260px);
    display: inline-flex; flex-direction: row; align-items: center; gap: 8px;
    padding: 5px 10px; border: 1px solid var(--border); border-radius: 6px;
    background: var(--surface2); cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s;
  }
  .ta-card:hover { border-color: rgba(199, 92, 92, 0.45); box-shadow: 0 1px 4px rgba(199, 92, 92, 0.1); }
  .ta-ico {
    flex-shrink: 0; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; line-height: 1; border-radius: 4px; background: var(--bg); border: 1px solid var(--border);
  }
  .ta-body { min-width: 0; flex: 1; display: flex; flex-direction: column; gap: 1px; }
  .ta-name {
    font-size: 0.72rem; font-weight: 600; color: var(--text);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-family: var(--mono); line-height: 1.3;
  }
  .ta-from { font-size: 0.6rem; color: var(--muted); line-height: 1.2; }
  .file-modal-toolbar { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
  .file-modal-dl {
    border: 1px solid rgba(199, 92, 92, 0.45); background: var(--surface); color: var(--oc-coral);
    font-size: 0.78rem; font-weight: 600; padding: 6px 12px; border-radius: 10px; cursor: pointer;
  }
  .file-modal-dl:hover { background: var(--oc-coral-soft); }
  .file-modal-dl:disabled { opacity: 0.45; cursor: not-allowed; }
  .file-modal-img-wrap { display: flex; justify-content: center; align-items: center; padding: 8px; }
  .file-modal-img { max-width: 100%; max-height: min(70vh, 720px); border-radius: 8px; }

  /* 底部仿输入区（只读装饰，对齐 OpenClaw） */
  .oc-input-bar {
    flex-shrink: 0; background: var(--surface);
    border-top: 1px solid var(--border); padding: 10px 16px 14px;
    display: flex; flex-direction: column; gap: 8px;
  }
  .oc-new-msg {
    align-self: center; display: none;
    border: 1px solid var(--border); background: var(--surface2);
    color: var(--muted); font-size: 0.78rem; padding: 6px 14px;
    border-radius: 999px; cursor: pointer;
  }
  .oc-new-msg:hover { color: var(--oc-coral); border-color: rgba(199, 92, 92, 0.4); }
  .oc-new-msg.visible { display: inline-flex; align-items: center; gap: 6px; }
  .oc-input-mock textarea {
    width: 100%; min-height: 52px; resize: none;
    border-radius: var(--radius-lg); border: 1px solid var(--border);
    background: var(--surface2); color: var(--muted);
    padding: 14px 16px; font-size: 0.88rem; font-family: var(--font);
    line-height: 1.45;
  }
  .oc-input-mock textarea:focus { outline: 2px solid rgba(199, 92, 92, 0.25); outline-offset: 0; }
  #grading-pane { width: 300px; border-left: 1px solid var(--border); overflow-y: auto; padding: 16px 18px; flex-shrink: 0; min-height: 0; background: var(--surface); }
  #grading-pane h3 { font-size: 0.78rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 12px; }

  #detail-body.detail-focus #grading-pane { display: none; }
  #app.sidebar-collapsed #sidebar { display: none; }

  /* ── OpenClaw-style transcript (chat layout) ── */
  .oc-chat { display: flex; flex-direction: column; gap: 18px; max-width: 920px; margin: 0 auto; }

  .oc-row { display: flex; width: 100%; align-items: flex-end; gap: 10px; }
  .oc-row-user { justify-content: flex-end; flex-wrap: nowrap; }
  .oc-row-assistant { justify-content: flex-start; align-items: flex-start; }

  .oc-user-wrap { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; max-width: min(88%, 640px); }
  .oc-user-time-row { width: 100%; display: flex; justify-content: flex-end; margin-bottom: 2px; }
  .oc-user-time {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.7rem; font-weight: 500; color: var(--muted);
    letter-spacing: 0.02em;
    padding: 3px 10px; border-radius: 999px;
    background: var(--surface2); border: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
  }
  body.theme-dark .oc-user-time { background: var(--surface2); }
  .oc-user-bubble {
    background: var(--oc-user-bubble);
    border: 1px solid var(--oc-user-border);
    border-radius: 18px 18px 6px 18px;
    padding: 12px 16px;
    font-size: 0.9rem;
    line-height: 1.65;
    color: var(--text);
    white-space: normal;
    word-break: break-word;
    box-shadow: 0 1px 0 rgba(0,0,0,0.03);
  }
  .oc-user-bubble .oc-user-md { border: none; padding: 0; margin: 0; }
  .oc-user-bubble .oc-user-md p { margin: 0 0 8px; }
  .oc-user-bubble .oc-user-md p:last-child { margin-bottom: 0; }
  .oc-user-bubble .oc-user-md ul, .oc-user-bubble .oc-user-md ol { margin: 6px 0 8px; padding-left: 1.35em; }
  .oc-user-bubble .oc-user-md li { margin: 3px 0; }
  .oc-user-bubble .oc-user-md h1, .oc-user-bubble .oc-user-md h2, .oc-user-bubble .oc-user-md h3 { margin: 10px 0 6px; font-size: 1em; }
  .oc-user-bubble .oc-user-md pre { margin: 8px 0; }
  .oc-user-bubble .oc-inline-code {
    font-family: var(--mono);
    font-size: 0.84em;
    background: rgba(255,255,255,0.85);
    border: 1px solid rgba(199, 92, 92, 0.2);
    border-radius: 5px;
    padding: 1px 6px;
  }
  .oc-user-meta { font-size: 0.72rem; color: var(--muted); padding-right: 4px; display: flex; align-items: center; gap: 8px; }
  .oc-user-meta .oc-del { cursor: pointer; opacity: 0.45; font-size: 0.85rem; }
  .oc-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(145deg, var(--oc-coral), #a84848);
    color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; flex-shrink: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
  }

  .oc-assistant-wrap { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; max-width: min(92%, 720px); }
  .oc-chips { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
  .oc-chip {
    display: inline-flex; align-items: center; flex-wrap: wrap; gap: 6px;
    background: var(--oc-chip-bg);
    border: 1px solid var(--oc-chip-border);
    border-radius: 14px;
    padding: 7px 12px 7px 10px;
    font-size: 0.8rem;
    color: #374151;
    line-height: 1.45;
    box-shadow: 0 1px 0 rgba(0,0,0,0.04);
  }
  .oc-chip-bolt { color: var(--oc-bolt); font-size: 0.95rem; line-height: 1; flex-shrink: 0; }
  .oc-chip .oc-chip-name {
    font-family: var(--mono);
    font-size: 0.78rem;
    font-weight: 600;
    color: #4b5563;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    border-radius: 5px;
    padding: 1px 7px;
  }
  .oc-chip-output { border-color: rgba(199, 92, 92, 0.22); }
  .oc-chip-output .oc-chip-bolt { color: var(--oc-bolt); }

  .oc-step-expand {
    width: 100%;
    border: 1px dashed rgba(199, 92, 92, 0.35);
    border-radius: 12px;
    background: rgba(255,255,255,0.65);
    margin-top: 4px;
  }
  .oc-step-expand > summary {
    cursor: pointer;
    list-style: none;
    user-select: none;
    padding: 8px 12px;
    font-size: 0.76rem;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .oc-step-expand > summary::marker { display: none; }
  .oc-step-expand > summary .oc-step-arrow { font-size: 0.65rem; transition: transform 0.15s; }
  .oc-step-expand[open] > summary .oc-step-arrow { transform: rotate(90deg); }
  .oc-step-inner { padding: 0 10px 12px; border-top: 1px solid rgba(0,0,0,0.05); }
  .oc-step-inner .step-meta { border-radius: 8px 8px 0 0; margin: 8px 0 0; border: 1px solid var(--border); border-bottom: none; }
  .oc-step-inner .toolcall-block:first-of-type { border-top: none; }
  .oc-step-inner .parts { border: 1px solid var(--border); border-radius: 0 0 8px 8px; overflow: hidden; background: var(--surface); }

  .oc-final-bubble {
    background: var(--oc-final-bg);
    border: 1px solid var(--oc-final-border);
    border-radius: 16px 16px 16px 6px;
    padding: 2px 0 4px;
    max-width: min(92%, 720px);
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }
  .oc-final-bubble .response-md { border-top: none; }
  .oc-final-bubble .response-md:first-child { padding-top: 12px; }
  .oc-final-bubble .thinking-block:first-child { border-top: none; }
  .oc-final-bubble .response-md { padding-left: 16px; padding-right: 16px; }
  .oc-final-bubble details.thinking-block > summary { border-radius: 12px 12px 0 0; }

  .oc-chat .response-md code:not(pre code) {
    background: var(--md-inline-bg); color: #374151; border: 1px solid var(--border);
    padding: 2px 6px; border-radius: 6px; font-size: 0.86em;
  }
  body.theme-dark .oc-chat .response-md code:not(pre code) { color: #e5e7eb; }
  .oc-chat .response-md pre code { color: #e5e7eb; }

  /* Inner transcript blocks (shared) */
  .parts { display: flex; flex-direction: column; }
  .step-meta { padding: 8px 14px; border-top: 1px solid var(--border); background: #f8f9fc; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
  .step-tools { display: inline-flex; align-items: center; gap: 6px; font-family: var(--mono); font-size: 0.72rem; color: #4b5563; background: var(--oc-coral-soft); border: 1px solid rgba(199, 92, 92, 0.2); border-radius: 999px; padding: 2px 8px; }
  .step-hint { font-size: 0.75rem; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 180px; }
  .step-empty { padding: 10px 14px; color: #6b7280; font-size: 0.78rem; border-top: 1px dashed var(--border); }
  .step-num { background: var(--oc-coral-soft); color: var(--oc-coral); font-family: var(--mono); font-size: 0.68rem; padding: 1px 7px; border-radius: 999px; font-weight: 800; }

  /* ── Thinking ── */
  details.thinking-block { border-top: 1px solid var(--border); }
  details.thinking-block > summary { padding: 7px 14px; cursor: pointer; font-size: 0.74rem; color: #6b7280; background: var(--thinking-bg); list-style: none; display: flex; align-items: center; gap: 6px; user-select: none; }
  details.thinking-block > summary::marker { display: none; }
  details.thinking-block > summary .arrow { font-size: 0.6rem; transition: transform 0.15s; display: inline-block; flex-shrink: 0; }
  details.thinking-block[open] > summary .arrow { transform: rotate(90deg); }
  details.thinking-block > summary .th-preview { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.7; }
  .thinking-body { padding: 12px 14px; font-size: 0.82rem; line-height: 1.65; color: #4b5563; background: var(--thinking-bg); white-space: pre-wrap; word-break: break-word; border-top: 1px solid var(--border); }

  /* ── Tool call ── */
  .toolcall-block { border-top: 1px solid var(--border); background: var(--tool-bg); }
  .toolcall-header { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px 7px; }
  .tool-badge { display: inline-flex; align-items: center; gap: 5px; background: var(--oc-coral-soft); color: var(--oc-coral); font-family: var(--mono); font-size: 0.74rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
  .copy-btn { background: none; border: 1px solid var(--border); color: var(--muted); font-size: 0.68rem; padding: 2px 8px; border-radius: 4px; cursor: pointer; transition: all 0.15s; }
  .copy-btn:hover { background: var(--surface2); color: var(--text); }
  .copy-btn.copied { color: var(--green); border-color: var(--green); }

  /* Key-value args */
  .tc-args { padding: 0 14px 10px; display: flex; flex-direction: column; gap: 6px; }
  .tc-arg { display: flex; flex-direction: column; gap: 3px; }
  .tc-arg-key { font-family: var(--mono); font-size: 0.7rem; color: var(--accent2); font-weight: 600; }
  .tc-arg-val { font-family: var(--mono); font-size: 0.77rem; color: #c4b5fd; background: #0d1117; border: 1px solid var(--border); border-radius: 5px; padding: 4px 9px; word-break: break-all; }
  /* Long multiline arg */
  details.tc-arg-long { }
  details.tc-arg-long > summary { font-size: 0.72rem; color: var(--muted); list-style: none; cursor: pointer; display: flex; align-items: center; gap: 5px; padding: 3px 0; user-select: none; }
  details.tc-arg-long > summary::marker { display: none; }
  details.tc-arg-long > summary .arrow { font-size: 0.58rem; transition: transform 0.15s; display: inline-block; flex-shrink: 0; }
  details.tc-arg-long[open] > summary .arrow { transform: rotate(90deg); }
  details.tc-arg-long pre { background: #0d1117; border: 1px solid var(--border); border-radius: 5px; font-family: var(--mono); font-size: 0.75rem; line-height: 1.5; overflow: auto; max-height: 520px; margin: 0; }
  details.tc-arg-long pre code { padding: 10px 12px; display: block; }
  .arg-preview { font-size: 0.76rem; line-height: 1.6; color: var(--text); background: #f7f8fb; border: 1px solid var(--border); border-radius: 5px; padding: 8px 10px; white-space: pre-wrap; word-break: break-word; }
  .arg-preview.markdown { padding: 10px 12px; }

  /* ── Tool result ── */
  .result-inline { border-top: 1px solid var(--border); padding: 8px 14px; background: #f7f8fb; display: flex; flex-direction: column; gap: 4px; }
  .result-inline-title { display: inline-flex; width: fit-content; font-size: 0.72rem; font-weight: 700; color: #5f6368; background: #eceff3; border: 1px solid #d8dde6; border-radius: 999px; padding: 2px 8px; font-family: var(--mono); }
  .result-inline-text { font-size: 0.78rem; color: #4b5563; white-space: pre-wrap; word-break: break-word; }
  details.result-block { border-top: 1px solid var(--border); background: var(--result-bg); }
  details.result-block > summary { padding: 7px 14px; cursor: pointer; font-size: 0.74rem; color: var(--muted); list-style: none; display: flex; align-items: center; gap: 6px; user-select: none; }
  details.result-block > summary::marker { display: none; }
  details.result-block > summary .arrow { font-size: 0.6rem; transition: transform 0.15s; display: inline-block; flex-shrink: 0; }
  details.result-block[open] > summary .arrow { transform: rotate(90deg); }
  details.result-block > summary .result-tool-name { font-family: var(--mono); font-size: 0.72rem; color: var(--oc-coral); background: var(--oc-coral-soft); padding: 1px 7px; border-radius: 3px; flex-shrink: 0; }
  details.result-block > summary .result-preview { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; opacity: 0.7; font-size: 0.72rem; min-width: 0; }
  details.result-block > summary .file-preview-btn-sm { margin-left: auto; flex-shrink: 0; }
  .result-body { padding: 6px 14px 10px; }
  .result-body pre { background: #0d1117; border: 1px solid var(--border); border-radius: 6px; font-family: var(--mono); font-size: 0.75rem; line-height: 1.5; overflow: auto; max-height: 560px; margin: 0; }
  .result-body pre code { padding: 10px 12px; display: block; }
  .result-rich { display: flex; flex-direction: column; gap: 10px; }
  .result-kv-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
  .result-kv { background: #111527; border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; min-width: 0; }
  .result-kv-key { font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; }
  .result-kv-val { font-size: 0.79rem; color: var(--text); word-break: break-word; }
  .result-list { display: flex; flex-direction: column; gap: 8px; }
  .result-card { background: #111527; border: 1px solid var(--border); border-radius: 6px; padding: 10px 12px; }
  .result-card-title { font-size: 0.82rem; font-weight: 600; line-height: 1.45; color: var(--text); }
  .result-card-title a { color: var(--accent); text-decoration: none; }
  .result-card-title a:hover { text-decoration: underline; }
  .result-card-meta { font-size: 0.72rem; color: var(--muted); margin-top: 5px; }
  .result-card-desc { font-size: 0.78rem; color: #cbd5e1; margin-top: 6px; line-height: 1.55; white-space: pre-wrap; word-break: break-word; }
  .result-markdown-preview { background: #111527; border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; }
  .raw-json-wrap { margin-top: 2px; }
  .raw-json-wrap summary { cursor: pointer; color: var(--muted); font-size: 0.72rem; list-style: none; user-select: none; }
  .raw-json-wrap summary::marker { display: none; }
  .raw-json-wrap pre { margin-top: 8px; }

  .result-file-actions { padding: 8px 14px 0; display: flex; justify-content: flex-end; }
  .file-preview-btn, .file-preview-btn-sm {
    border: 1px solid rgba(199, 92, 92, 0.45); background: var(--surface);
    color: var(--oc-coral); font-size: 0.76rem; font-weight: 600;
    padding: 6px 12px; border-radius: 10px; cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .file-preview-btn:hover, .file-preview-btn-sm:hover {
    background: var(--oc-coral-soft); border-color: var(--oc-coral);
  }
  .file-preview-btn-sm { padding: 4px 10px; font-size: 0.7rem; }
  .toolcall-header { gap: 8px; flex-wrap: wrap; }
  .toolcall-header-actions { display: inline-flex; align-items: center; gap: 8px; margin-left: auto; }

  /* 文件预览弹窗 */
  .file-modal { position: fixed; inset: 0; z-index: 1000; display: none; align-items: center; justify-content: center; padding: 24px; }
  .file-modal.open { display: flex; }
  .file-modal-backdrop { position: absolute; inset: 0; background: rgba(15, 17, 21, 0.45); backdrop-filter: blur(2px); }
  .file-modal-panel {
    position: relative; max-width: min(96vw, 920px); width: 100%; max-height: min(88vh, 900px);
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg);
    box-shadow: 0 20px 50px rgba(0,0,0,0.18); display: flex; flex-direction: column; overflow: hidden;
  }
  .file-modal-header {
    display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
    padding: 14px 18px; border-bottom: 1px solid var(--border); flex-shrink: 0;
  }
  .file-modal-header > div:first-child { flex: 1; min-width: 0; }
  .file-modal-header h2 { font-size: 0.95rem; font-weight: 700; margin: 0; word-break: break-all; color: var(--text); }
  .file-modal-sub { font-size: 0.72rem; color: var(--muted); font-weight: 500; margin-top: 4px; }
  .file-modal-close {
    width: 36px; height: 36px; border-radius: 10px; border: 1px solid var(--border);
    background: var(--surface2); color: var(--muted); font-size: 1.25rem; line-height: 1; cursor: pointer; flex-shrink: 0;
  }
  .file-modal-close:hover { color: var(--oc-coral); border-color: rgba(199, 92, 92, 0.4); }
  .file-modal-body {
    flex: 1; overflow: auto; padding: 16px 18px; min-height: 120px;
    font-size: 0.88rem; background: var(--bg);
  }
  .file-modal-body .response-md { border: none; padding: 0; }
  .file-modal-body pre { margin: 0; border-radius: 10px; max-height: none; }
  .file-modal-table-wrap { overflow: auto; max-height: min(70vh, 720px); border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
  .file-modal-csv { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
  .file-modal-csv th, .file-modal-csv td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  .file-modal-csv thead { position: sticky; top: 0; background: var(--surface2); z-index: 1; }
  .file-modal-csv tbody tr:nth-child(even) { background: rgba(0,0,0,0.02); }
  body.theme-dark .file-modal-csv tbody tr:nth-child(even) { background: rgba(255,255,255,0.02); }
  .file-modal-pre { margin: 0; white-space: pre-wrap; word-break: break-word; font-family: var(--mono); font-size: 0.82rem; line-height: 1.55; }

  /* 可点击文件路径（exec / 输出中的 *.md 等） */
  button.path-link {
    display: inline; background: none; border: none; padding: 0; margin: 0;
    color: var(--oc-coral); text-decoration: underline; cursor: pointer;
    font: inherit; font-family: inherit;
  }
  .toolcall-block pre code .path-link, .result-body pre code .path-link {
    font-family: var(--mono);
  }
  button.path-link:hover { color: var(--accent2); }

  /* ── Markdown response ── */
  .response-md { padding: 14px 18px; font-size: 0.9rem; line-height: 1.75; border-top: 1px solid var(--border); word-break: break-word; }
  .response-md p { margin: 0 0 10px; }
  .response-md p:last-child { margin-bottom: 0; }
  .response-md h1,.response-md h2,.response-md h3,.response-md h4 { margin: 14px 0 8px; font-weight: 700; line-height: 1.3; }
  .response-md h1 { font-size: 1.25rem; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  .response-md h2 { font-size: 1.1rem; }
  .response-md h3 { font-size: 0.98rem; color: var(--oc-coral); }
  .response-md ul,.response-md ol { padding-left: 1.4em; margin: 6px 0 10px; }
  .response-md li { margin: 3px 0; }
  .response-md code { font-family: var(--mono); font-size: 0.83em; background: var(--md-inline-bg); padding: 2px 6px; border-radius: 5px; color: #374151; border: 1px solid var(--border); }
  body.theme-dark .response-md code { background: #1a1f3a; color: #c4b5fd; border-color: transparent; }
  .response-md pre { margin: 10px 0; border-radius: 7px; overflow: hidden; border: 1px solid var(--border); }
  .response-md pre code { background: #0d1117; padding: 12px 14px; display: block; font-size: 0.8rem; line-height: 1.55; color: var(--text); overflow-x: auto; border-radius: 0; }
  .response-md blockquote { border-left: 3px solid var(--accent); padding: 4px 12px; margin: 8px 0; color: var(--muted); }
  .response-md table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 0.85rem; }
  .response-md th,.response-md td { border: 1px solid var(--border); padding: 6px 10px; text-align: left; }
  .response-md th { background: var(--surface2); font-weight: 600; }
  .response-md a { color: var(--oc-coral); text-decoration: none; }
  .response-md a:hover { text-decoration: underline; }
  .response-md strong { color: var(--text); font-weight: 700; }
  .response-md hr { border: none; border-top: 1px solid var(--border); margin: 14px 0; }
  .response-md:first-child { border-top: none; }
  .step-followup { border-top: 1px solid var(--border); }

  /* Code block header (lang + copy) */
  .code-block-wrapper { border: 1px solid var(--border); border-radius: 7px; overflow: hidden; margin: 10px 0; }
  .code-block-header { display: flex; align-items: center; justify-content: space-between; padding: 5px 12px; background: #161b27; font-size: 0.72rem; }
  .code-block-lang { color: var(--muted); font-family: var(--mono); }
  .code-block-copy { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 0.72rem; padding: 2px 6px; border-radius: 3px; }
  .code-block-copy:hover { color: var(--text); background: var(--surface2); }
  .code-block-wrapper pre { margin: 0; border: none; border-radius: 0; }
  .code-block-wrapper pre code { border-radius: 0; }

  /* ── Grading panel ── */
  .grading-score-big { font-size: 2rem; font-weight: 800; margin-bottom: 4px; }
  .grading-breakdown { margin-top: 12px; display: flex; flex-direction: column; gap: 6px; }
  .gb-row { display: flex; justify-content: space-between; font-size: 0.8rem; padding: 5px 8px; background: var(--surface2); border-radius: 4px; }
  .gb-key { color: var(--muted); }
  .gb-val { font-weight: 600; }
  .grading-notes { margin-top: 12px; font-size: 0.8rem; color: var(--muted); background: var(--surface2); padding: 8px; border-radius: 4px; line-height: 1.5; }

  .usage-block { margin-top: 16px; }
  .usage-block h3 { font-size: 0.78rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 10px; }

  /* ── Empty / loading states ── */
  #empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--muted); gap: 10px; }
  #empty-state .em-icon { font-size: 3rem; }
  .loading { text-align: center; padding: 40px; color: var(--muted); }
  .leaderboard-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
  .leaderboard-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .leaderboard-meta { font-size: 0.76rem; color: var(--muted); }
  .leaderboard-sort { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .leaderboard-btn { border: 1px solid var(--border); background: var(--surface2); color: var(--text); border-radius: 999px; padding: 5px 10px; font-size: 0.72rem; cursor: pointer; }
  .leaderboard-btn:hover { border-color: var(--oc-coral); color: var(--oc-coral); }
  .leaderboard-btn.active { background: var(--oc-coral-soft); border-color: #efc9c9; color: var(--oc-coral); font-weight: 600; }
  .leaderboard-table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }
  .leaderboard-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
  .leaderboard-table th, .leaderboard-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); text-align: left; white-space: nowrap; }
  .leaderboard-table th { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; background: var(--surface2); position: sticky; top: 0; z-index: 1; }
  .leaderboard-table tr:last-child td { border-bottom: none; }
  .leaderboard-table .mono { font-family: var(--mono); font-size: 0.72rem; }
  .leaderboard-table .model-name { max-width: 340px; overflow: hidden; text-overflow: ellipsis; }
  .leaderboard-table .is-link { color: var(--oc-coral); cursor: pointer; font-weight: 600; }
  .leaderboard-table .is-link:hover { text-decoration: underline; }
  .leaderboard-empty { padding: 28px 12px; text-align: center; color: var(--muted); }
  .leaderboard-top { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-bottom: 12px; }
  .leaderboard-top-card { background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; }
  .leaderboard-top-card .k { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
  .leaderboard-top-card .v { margin-top: 4px; font-size: 0.86rem; font-weight: 700; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<header id="oc-header">
  <div class="oc-nav-top">
    <div class="oc-nav-left">
      <button type="button" id="back-btn" onclick="showTaskGrid()" title="返回任务列表">←</button>
      <div class="oc-crumb-main" id="oc-crumb-wrap">
        <span class="oc-brand">PinchBench</span>
        <span class="oc-sep">›</span>
        <span class="oc-page" id="oc-page-title">结果</span>
      </div>
    </div>
    <div class="oc-nav-right">
      <div class="oc-search-pill" id="oc-search-pill" role="search"><span class="oc-kbd">⌘K</span> 搜索...</div>
      <button type="button" class="oc-ico" id="oc-btn-view" title="侧栏" aria-label="侧栏">▭</button>
      <button type="button" class="oc-ico" id="theme-btn" title="切换主题" aria-label="主题">☀</button>
    </div>
  </div>
  <div id="oc-subbar" class="oc-subbar is-hidden">
    <div class="oc-subbar-left">
      <div class="oc-pill" id="pill-identity"><span class="oc-pill-muted">来源</span><span id="pill-identity-v">—</span></div>
      <div class="oc-pill" id="pill-model"><span class="oc-pill-muted">模型</span><span id="pill-model-v">—</span></div>
      <div class="oc-pill" id="pill-meta"><span class="oc-pill-muted">配置</span><span id="pill-meta-v">—</span></div>
    </div>
    <div class="oc-subbar-right">
      <button type="button" class="oc-ico-sm" id="btn-refresh" title="刷新">↻</button>
      <span class="oc-vsep"></span>
      <button type="button" class="oc-ico-sm oc-accent" id="btn-grading" title="评分">📊</button>
      <button type="button" class="oc-ico-sm oc-accent" id="btn-tools" title="工具步骤">🛠</button>
      <button type="button" class="oc-ico-sm oc-accent" id="btn-focus" title="宽屏对话">⛶</button>
      <button type="button" class="oc-ico-sm oc-accent" id="btn-history" title="回到顶部">↑</button>
    </div>
  </div>
</header>

<div id="app">
  <!-- Sidebar -->
  <div id="sidebar">
    <div id="sidebar-header">
      <div class="sidebar-title">运行记录</div>
      <button type="button" class="sidebar-btn" id="sidebar-leaderboard-btn">🏆 榜单</button>
    </div>
    <div id="run-list"><div class="loading">加载中...</div></div>
  </div>

  <!-- Main -->
  <div id="main">
    <!-- Task grid view -->
    <div id="task-panel">
      <div id="empty-state">
        <div class="em-icon">🏆</div>
        <div>加载模型榜单中...</div>
      </div>
    </div>

    <!-- Detail view (conversation) -->
    <div id="detail-pane">
      <div id="detail-header">
        <div class="dh-crumb" id="dh-crumb"></div>
        <div class="dh-id" id="dh-id"></div>
        <div class="dh-name" id="dh-name"></div>
        <div class="dh-stats" id="dh-stats"></div>
        <div id="dh-actions" style="margin-top:10px"></div>
      </div>
      <div id="detail-body">
        <div id="transcript-wrap">
          <div id="transcript-pane"><div class="loading">加载对话中...</div></div>
          <div id="transcript-artifacts" class="transcript-artifacts is-empty">
            <div class="ta-head">本次输出</div>
            <div class="ta-strip" id="ta-strip"></div>
          </div>
          <div id="transcript-input-bar" class="oc-input-bar" style="display:none">
            <button type="button" class="oc-new-msg" id="btn-new-messages" aria-hidden="true">↓ 新消息</button>
            <div class="oc-input-mock">
              <textarea readonly rows="2" placeholder="Message Assistant (Enter to send)"></textarea>
            </div>
          </div>
        </div>
        <div id="grading-pane"></div>
      </div>
    </div>
  </div>
</div>

<div id="file-preview-modal" class="file-modal" aria-hidden="true">
  <div class="file-modal-backdrop" id="file-modal-backdrop"></div>
  <div class="file-modal-panel" role="dialog" aria-modal="true" aria-labelledby="file-modal-title">
    <div class="file-modal-header">
      <div>
        <h2 id="file-modal-title">文件预览</h2>
        <div id="file-modal-sub" class="file-modal-sub"></div>
      </div>
      <div class="file-modal-toolbar">
        <button type="button" class="file-modal-dl" id="file-modal-download" style="display:none">下载</button>
        <button type="button" class="file-modal-close" id="file-modal-close" aria-label="关闭">×</button>
      </div>
    </div>
    <div id="file-modal-body" class="file-modal-body"></div>
  </div>
</div>

<script>
// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let currentRunId = null;
let currentRunData = null;
let currentTaskId = null;
let currentTranscriptData = null;
let rerunJobs = {};
let leaderboardSortBy = 'score';
let leaderboardResultKeyFilter = '*';
let taskCategoryFilter = '*';

function setSubbarVisible(show) {
  const el = document.getElementById('oc-subbar');
  if (el) el.classList.toggle('is-hidden', !show);
}

function taskCategoryOf(task) {
  return task?.frontmatter?.category || task?.category || 'uncategorized';
}

function filterLeaderboardRowsByKey(rows) {
  if (leaderboardResultKeyFilter === '*') return [...(rows || [])];
  return (rows || []).filter(r => String(r.result_key || 'all') === leaderboardResultKeyFilter);
}

function updatePillsForRun() {
  if (!currentRunData) return;
  const modelSlug = currentRunData.model_slug || currentRunId;
  const resultKey = currentRunData.result_key || 'all';
  const tasks = currentRunData.tasks || [];
  const scored = tasks.filter(t => t.grading);
  const totalScore = scored.reduce((s, t) => s + (t.grading.mean || 0), 0);
  const idv = document.getElementById('pill-identity-v');
  const mv = document.getElementById('pill-model-v');
  const meta = document.getElementById('pill-meta-v');
  if (idv) idv.textContent = `模型 ${modelSlug} / ${resultKey}`;
  if (mv) mv.textContent = currentRunData.model || '—';
  if (meta) {
    meta.textContent = scored.length
      ? `总分 ${totalScore.toFixed(2)}/${scored.length} · ${tasks.length} 任务`
      : `${tasks.length} 任务`;
  }
}

function updatePillsForTask(task, transcriptMeta) {
  const taskId = currentTaskId || '';
  const idv = document.getElementById('pill-identity-v');
  const mv = document.getElementById('pill-model-v');
  const metaEl = document.getElementById('pill-meta-v');
  const modelSlug = currentRunData?.model_slug || currentRunId;
  if (idv) idv.textContent = `模型 ${modelSlug} · ${taskId}`;
  let modelLine = currentRunData?.model || '—';
  if (transcriptMeta) {
    const prov = transcriptMeta.provider || '';
    const mid = transcriptMeta.model_id || '';
    if (mid) modelLine = (prov ? `${prov}: ` : '') + mid;
  }
  if (mv) mv.textContent = modelLine;
  let meta = '';
  if (task) {
    const score = task.grading?.mean;
    meta = score !== undefined ? `评分 ${score.toFixed(2)} / ${task.grading?.max ?? 1}` : 'Default (low)';
    if (task.execution_time != null) meta += ` · ${task.execution_time.toFixed(1)}s`;
  }
  if (metaEl) metaEl.textContent = meta || '—';
}

function applyTheme(dark) {
  document.body.classList.toggle('theme-dark', !!dark);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = dark ? '☾' : '☀';
  try { localStorage.setItem('pinchbench-theme', dark ? 'dark' : 'light'); } catch (e) {}
}

function setupChromeHandlers() {
  setupFilePreviewModal();
  document.getElementById('transcript-wrap')?.addEventListener('click', (e) => {
    const btn = e.target.closest('button.path-link');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    const fn = btn.getAttribute('data-file');
    if (fn) openFileFromTranscriptIndex(fn);
  });
  const themeBtn = document.getElementById('theme-btn');
  if (themeBtn) {
    let dark = false;
    try { dark = localStorage.getItem('pinchbench-theme') === 'dark'; } catch (e) {}
    applyTheme(dark);
    themeBtn.addEventListener('click', () => applyTheme(!document.body.classList.contains('theme-dark')));
  }
  const viewBtn = document.getElementById('oc-btn-view');
  if (viewBtn) {
    viewBtn.addEventListener('click', () => {
      document.getElementById('app')?.classList.toggle('sidebar-collapsed');
    });
  }
  document.getElementById('btn-refresh')?.addEventListener('click', async () => {
    if (currentTaskId && currentRunId) {
      document.getElementById('transcript-pane').innerHTML = '<div class="loading">刷新中...</div>';
      try {
        currentRunData = await apiFetch(`/api/runs/${currentRunId}`);
        currentTranscriptData = await apiFetch(`/api/transcript/${currentRunId}/${currentTaskId}`);
        const task = (currentRunData?.tasks || []).find(t => t.task_id === currentTaskId);
        renderDetailActions(task);
        renderGrading(task);
        renderTranscript(currentTranscriptData);
      } catch (e) {
        document.getElementById('transcript-pane').innerHTML = `<div class="loading">刷新失败: ${e.message}</div>`;
      }
    } else if (currentRunId) {
      await refreshCurrentRun(null);
    }
  });
  document.getElementById('btn-grading')?.addEventListener('click', () => {
    document.getElementById('grading-pane')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
  document.getElementById('btn-tools')?.addEventListener('click', () => {
    const pane = document.getElementById('transcript-pane');
    const first = pane?.querySelector('.oc-chip, .oc-step-expand');
    first?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
  document.getElementById('btn-focus')?.addEventListener('click', () => {
    document.getElementById('detail-body')?.classList.toggle('detail-focus');
  });
  document.getElementById('btn-history')?.addEventListener('click', () => {
    document.getElementById('transcript-pane')?.scrollTo({ top: 0, behavior: 'smooth' });
  });
  document.getElementById('oc-search-pill')?.addEventListener('click', () => {
    /* 占位：与 OpenClaw 搜索条视觉一致 */
  });
  document.getElementById('sidebar-leaderboard-btn')?.addEventListener('click', () => {
    showLeaderboard().catch(err => {
      const panel = document.getElementById('task-panel');
      if (panel) panel.innerHTML = `<div class="loading">加载榜单失败: ${escHtml(err.message || String(err))}</div>`;
    });
  });
  window.addEventListener('keydown', (ev) => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') {
      ev.preventDefault();
      document.getElementById('oc-search-pill')?.animate(
        [{ boxShadow: '0 0 0 0 rgba(199,92,92,0.4)' }, { boxShadow: '0 0 0 6px rgba(199,92,92,0)' }],
        { duration: 400 }
      );
    }
  });
}

function setupTranscriptScroll() {
  const pane = document.getElementById('transcript-pane');
  const btn = document.getElementById('btn-new-messages');
  if (!pane || !btn) return;
  if (pane._ocScroll) pane.removeEventListener('scroll', pane._ocScroll);
  const onScroll = () => {
    const gap = pane.scrollHeight - pane.scrollTop - pane.clientHeight;
    const nearBottom = gap < 72;
    const tall = pane.scrollHeight > pane.clientHeight + 48;
    btn.classList.toggle('visible', !nearBottom && tall);
  };
  pane._ocScroll = onScroll;
  pane.addEventListener('scroll', onScroll);
  btn.onclick = () => pane.scrollTo({ top: pane.scrollHeight, behavior: 'smooth' });
  onScroll();
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
async function init() {
  setupChromeHandlers();
  const runs = await apiFetch('/api/runs');
  renderRunList(runs);
  await showLeaderboard();
}

async function apiFetch(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function apiPost(path, payload = {}) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    let msg = `HTTP ${r.status}`;
    try {
      const data = await r.json();
      if (data?.error) msg = data.error;
    } catch (e) {}
    throw new Error(msg);
  }
  return r.json();
}

function rerunJobForTask(taskId) {
  const job = rerunJobs[taskId];
  return job && ['queued', 'running'].includes(job.status) ? job : null;
}

function rerunLabel(taskId) {
  const job = rerunJobs[taskId];
  if (!job) return '重新运行';
  if (job.status === 'queued') return '排队中...';
  if (job.status === 'running') return '运行中...';
  if (job.status === 'completed') return '已更新';
  if (job.status === 'failed') return '重试失败';
  return '重新运行';
}

function leaderboardComparator(sortBy) {
  if (sortBy === 'speed') {
    return (a, b) => (a.avg_task_seconds || 0) - (b.avg_task_seconds || 0)
      || (b.score_pct || 0) - (a.score_pct || 0)
      || (a.total_cost_usd || 0) - (b.total_cost_usd || 0);
  }
  if (sortBy === 'cost') {
    return (a, b) => (a.total_cost_usd || 0) - (b.total_cost_usd || 0)
      || (b.score_pct || 0) - (a.score_pct || 0)
      || (a.avg_task_seconds || 0) - (b.avg_task_seconds || 0);
  }
  return (a, b) => (b.score_pct || 0) - (a.score_pct || 0)
    || (a.avg_task_seconds || 0) - (b.avg_task_seconds || 0)
    || (a.total_cost_usd || 0) - (b.total_cost_usd || 0);
}

function sortLeaderboardRows(rows) {
  return [...(rows || [])].sort(leaderboardComparator(leaderboardSortBy));
}

function formatTime(sec) {
  if (sec == null || Number.isNaN(sec)) return '—';
  return `${Number(sec).toFixed(2)}s`;
}

function formatCurrency(v, digits = 4) {
  if (v == null || Number.isNaN(v)) return '—';
  return `$${Number(v).toFixed(digits)}`;
}

function renderLeaderboard(rows) {
  const panel = document.getElementById('task-panel');
  if (!panel) return;
  const keyOptions = Array.from(new Set((rows || []).map(r => String(r.result_key || 'all')))).sort();
  const filteredRows = filterLeaderboardRowsByKey(rows);
  const sorted = sortLeaderboardRows(filteredRows);
  const newestTs = Math.max(...sorted.map(r => Number(r.timestamp || 0)), 0);
  const newestText = newestTs ? new Date(newestTs * 1000).toLocaleString('zh-CN') : '—';
  const sortLabel = leaderboardSortBy === 'speed' ? '速度优先（平均耗时更低）'
    : leaderboardSortBy === 'cost' ? '成本优先（总费用更低）'
    : '得分优先（综合得分更高）';
  const keyButtons = ['*', ...keyOptions].map(key => {
    const label = key === '*' ? '全部' : key;
    return `<button type="button" class="leaderboard-btn ${leaderboardResultKeyFilter === key ? 'active' : ''}" onclick="setLeaderboardResultKeyFilter('${key}')">${label}</button>`;
  }).join('');

  if (!sorted.length) {
    panel.innerHTML = `
      <div class="leaderboard-wrap">
        <div class="leaderboard-head">
          <div class="section-title" style="margin-bottom:0">模型榜单</div>
          <div class="leaderboard-meta">暂无可用评测结果</div>
        </div>
        <div class="leaderboard-sort" style="margin-bottom:12px">
          <span class="leaderboard-meta">结果键：</span>
          ${keyButtons}
        </div>
        <div class="leaderboard-empty">先跑完至少一个模型的 benchmark，再回来查看榜单。</div>
      </div>
    `;
    return;
  }

  const bestScore = sorted[0];
  const bestSpeed = [...sorted].sort(leaderboardComparator('speed'))[0];
  const bestCost = [...sorted].sort(leaderboardComparator('cost'))[0];
  const topCards = `
    <div class="leaderboard-top">
      <div class="leaderboard-top-card">
        <div class="k">得分最佳</div>
        <div class="v">${escHtml(bestScore.model_slug || bestScore.run_id)} · ${(bestScore.score_pct || 0).toFixed(2)}%</div>
      </div>
      <div class="leaderboard-top-card">
        <div class="k">速度最佳</div>
        <div class="v">${escHtml(bestSpeed.model_slug || bestSpeed.run_id)} · ${formatTime(bestSpeed.avg_task_seconds)}</div>
      </div>
      <div class="leaderboard-top-card">
        <div class="k">成本最佳</div>
        <div class="v">${escHtml(bestCost.model_slug || bestCost.run_id)} · ${formatCurrency(bestCost.total_cost_usd, 6)}</div>
      </div>
    </div>
  `;

  const rowsHtml = sorted.map((r, idx) => {
    const scorePct = Number(r.score_pct || 0);
    const scoreClass = scorePct >= 80 ? 'score-high' : scorePct >= 50 ? 'score-mid' : 'score-low';
    return `
    <tr>
      <td>${idx + 1}</td>
      <td class="mono is-link" onclick="selectRun('${String(r.run_id || '')}')">${escHtml(String(r.model_slug || r.run_id || ''))}</td>
      <td class="model-name" title="${escHtml(String(r.model || ''))}">${escHtml(String(r.model || '—'))}</td>
      <td><span class="${scoreClass}">${scorePct.toFixed(2)}%</span> (${Number(r.total_score || 0).toFixed(2)}/${Number(r.max_score || 0)})</td>
      <td>${formatTime(Number(r.avg_task_seconds || 0))}</td>
      <td>${formatTime(Number(r.total_execution_seconds || 0))}</td>
      <td>${formatCurrency(Number(r.total_cost_usd || 0), 6)}</td>
      <td>${formatCurrency(Number(r.avg_cost_per_task_usd || 0), 6)}</td>
      <td>${Number(r.success_task_count || 0)}/${Number(r.task_count || 0)}</td>
      <td>${Number(r.task_count || 0)}</td>
      <td>${r.timestamp ? new Date(Number(r.timestamp) * 1000).toLocaleDateString('zh-CN') : '—'}</td>
    </tr>
  `;
  }).join('');

  panel.innerHTML = `
    <div class="leaderboard-wrap">
      <div class="leaderboard-head">
        <div>
          <div class="section-title" style="margin-bottom:4px">模型榜单</div>
          <div class="leaderboard-meta">按「得分 / 速度 / 成本」对比各模型最新评测 · 最新数据 ${newestText}</div>
        </div>
        <div class="leaderboard-sort">
          <span class="leaderboard-meta">排序：</span>
          <button type="button" class="leaderboard-btn ${leaderboardSortBy === 'score' ? 'active' : ''}" onclick="setLeaderboardSort('score')">得分</button>
          <button type="button" class="leaderboard-btn ${leaderboardSortBy === 'speed' ? 'active' : ''}" onclick="setLeaderboardSort('speed')">速度</button>
          <button type="button" class="leaderboard-btn ${leaderboardSortBy === 'cost' ? 'active' : ''}" onclick="setLeaderboardSort('cost')">成本</button>
        </div>
      </div>
      <div class="leaderboard-sort" style="margin-bottom:12px">
        <span class="leaderboard-meta">结果键：</span>
        ${keyButtons}
      </div>
      ${topCards}
      <div class="leaderboard-meta" style="margin-bottom:8px">${sortLabel}</div>
      <div class="leaderboard-table-wrap">
        <table class="leaderboard-table">
          <thead>
            <tr>
              <th>#</th>
              <th>模型Slug</th>
              <th>模型</th>
              <th>得分</th>
              <th>平均耗时</th>
              <th>总耗时</th>
              <th>总成本</th>
              <th>单任务成本</th>
              <th>成功任务</th>
              <th>任务数</th>
              <th>日期</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
    </div>
  `;
}

async function showLeaderboard() {
  const panel = document.getElementById('task-panel');
  if (!panel) return;
  currentRunId = null;
  currentRunData = null;
  currentTaskId = null;
  currentTranscriptData = null;
  document.querySelectorAll('.run-item').forEach(e => e.classList.remove('active'));
  panel.style.display = 'block';
  document.getElementById('detail-pane').classList.remove('open');
  document.getElementById('back-btn').style.display = 'none';
  setSubbarVisible(false);
  document.getElementById('oc-page-title').textContent = '榜单';
  panel.innerHTML = '<div class="loading">加载榜单...</div>';
  const rows = await apiFetch('/api/leaderboard');
  renderLeaderboard(rows);
}

async function setLeaderboardSort(sortBy) {
  leaderboardSortBy = sortBy;
  const rows = await apiFetch('/api/leaderboard');
  renderLeaderboard(rows);
}

async function setLeaderboardResultKeyFilter(resultKey) {
  leaderboardResultKeyFilter = resultKey;
  const rows = await apiFetch('/api/leaderboard');
  renderLeaderboard(rows);
}

function setTaskCategoryFilter(categoryKey) {
  taskCategoryFilter = categoryKey;
  if (currentRunData) renderTaskGrid(currentRunData);
}

function renderDetailActions(task) {
  const el = document.getElementById('dh-actions');
  if (!el) return;
  if (!task) {
    el.innerHTML = '';
    return;
  }
  const disabled = rerunJobForTask(task.task_id) ? 'disabled' : '';
  el.innerHTML = `<button type="button" class="action-btn is-primary" ${disabled} onclick="rerunTask('${task.task_id}', event)">${rerunLabel(task.task_id)}</button>`;
}

async function refreshCurrentRun(reopenTaskId = null) {
  if (!currentRunId) return;
  const activeTask = reopenTaskId === null ? currentTaskId : reopenTaskId;
  currentRunData = await apiFetch(`/api/runs/${currentRunId}`);
  const runs = await apiFetch('/api/runs');
  renderRunList(runs);
  document.querySelectorAll('.run-item').forEach(e => e.classList.remove('active'));
  const ri = document.getElementById(`ri-${currentRunId}`);
  if (ri) ri.classList.add('active');
  if (activeTask) {
    await openTask(activeTask);
  } else {
    renderTaskGrid(currentRunData);
    updatePillsForRun();
  }
}

async function pollRerunJob(jobId, taskId) {
  while (true) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    const job = await apiFetch(`/api/rerun-jobs/${jobId}`);
    rerunJobs[taskId] = job;
    if (currentTaskId === taskId) {
      const task = (currentRunData?.tasks || []).find(t => t.task_id === taskId);
      renderDetailActions(task);
    } else if (!currentTaskId && currentRunData) {
      renderTaskGrid(currentRunData);
    }
    if (job.status === 'completed') {
      await refreshCurrentRun(currentTaskId === taskId ? taskId : null);
      setTimeout(() => {
        delete rerunJobs[taskId];
        if (currentTaskId === taskId) {
          const task = (currentRunData?.tasks || []).find(t => t.task_id === taskId);
          renderDetailActions(task);
        } else if (!currentTaskId && currentRunData) {
          renderTaskGrid(currentRunData);
        }
      }, 2500);
      return;
    }
    if (job.status === 'failed') {
      alert(`任务重跑失败: ${job.error || '未知错误'}`);
      return;
    }
  }
}

async function rerunTask(taskId, ev) {
  if (ev) {
    ev.preventDefault();
    ev.stopPropagation();
  }
  if (!currentRunId || rerunJobForTask(taskId)) return;
  const modelSlug = currentRunData?.model_slug || currentRunId;
  const ok = confirm(`重新运行 ${taskId}？\n只会更新当前模型 ${modelSlug} 的该任务记录和 transcript，其它任务不变。`);
  if (!ok) return;
  const job = await apiPost(`/api/runs/${currentRunId}/tasks/${taskId}/rerun`);
  rerunJobs[taskId] = job;
  if (currentTaskId === taskId) {
    const task = (currentRunData?.tasks || []).find(t => t.task_id === taskId);
    renderDetailActions(task);
  } else if (!currentTaskId && currentRunData) {
    renderTaskGrid(currentRunData);
  }
  pollRerunJob(job.job_id, taskId).catch(err => alert(`轮询重跑状态失败: ${err.message}`));
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------
function renderRunList(runs) {
  const el = document.getElementById('run-list');
  if (!runs.length) { el.innerHTML = '<div class="loading">无数据</div>'; return; }
  el.innerHTML = runs.map(r => {
    const pct = r.max_score ? Math.round(r.total_score / r.max_score * 100) : 0;
    const date = r.timestamp ? new Date(r.timestamp * 1000).toLocaleDateString('zh-CN') : '';
    const modelSlug = r.model_slug || r.run_id;
    const resultKey = r.result_key ? ` / ${r.result_key}` : '';
    const displayPath = r.display_path ? ` · ${r.display_path}` : '';
    return `<div class="run-item" id="ri-${r.run_id}" onclick="selectRun('${r.run_id}')">
      <div class="run-id">${modelSlug}${resultKey}</div>
      <div class="run-model">${r.model}</div>
      <div class="run-score">${r.total_score}/${r.max_score} (${pct}%) · ${date}${displayPath}</div>
    </div>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Run selection → Task grid
// ---------------------------------------------------------------------------
async function selectRun(runId) {
  currentRunId = runId;
  taskCategoryFilter = '*';
  document.querySelectorAll('.run-item').forEach(e => e.classList.remove('active'));
  const ri = document.getElementById(`ri-${runId}`);
  if (ri) ri.classList.add('active');

  document.getElementById('task-panel').style.display = 'block';
  document.getElementById('detail-pane').classList.remove('open');
  document.getElementById('back-btn').style.display = 'none';
  document.getElementById('task-panel').innerHTML = '<div class="loading">加载任务列表...</div>';

  try {
    currentRunData = await apiFetch(`/api/runs/${runId}`);
    renderTaskGrid(currentRunData);
    document.getElementById('oc-page-title').textContent = '任务';
    setSubbarVisible(true);
    updatePillsForRun();
  } catch(e) {
    document.getElementById('task-panel').innerHTML = `<div class="loading">加载失败: ${e.message}</div>`;
  }
}

function renderTaskGrid(data) {
  const allTasks = data.tasks || [];
  const categoryOptions = Array.from(new Set(allTasks.map(taskCategoryOf))).sort();
  const tasks = taskCategoryFilter === '*' ? allTasks : allTasks.filter(t => taskCategoryOf(t) === taskCategoryFilter);

  // Summary
  const scored = tasks.filter(t => t.grading);
  const totalScore = scored.reduce((s, t) => s + (t.grading.mean || 0), 0);
  const successCount = tasks.filter(t => t.status === 'success').length;
  const timeoutCount = tasks.filter(t => t.timed_out).length;
  const totalCost = tasks.reduce((s, t) => s + (t.usage?.cost_usd || 0), 0);
  const totalTokens = tasks.reduce((s, t) => s + (t.usage?.total_tokens || 0), 0);

  const categoryButtons = ['*', ...categoryOptions].map(key => {
    const label = key === '*' ? '全部' : key;
    return `<button type="button" class="leaderboard-btn ${taskCategoryFilter === key ? 'active' : ''}" onclick="setTaskCategoryFilter('${key}')">${label}</button>`;
  }).join('');

  const summaryHtml = `<div class="run-summary-head">
    <div class="section-title">运行汇总</div>
    <button type="button" class="action-btn is-primary" onclick="refreshCurrentRun(null)">刷新汇总</button>
  </div><div id="run-summary">
    <div class="stat"><div class="stat-val">${tasks.length}</div><div class="stat-label">总任务</div></div>
    <div class="stat"><div class="stat-val score-high">${successCount}</div><div class="stat-label">成功</div></div>
    <div class="stat"><div class="stat-val score-low">${timeoutCount}</div><div class="stat-label">超时</div></div>
    <div class="stat"><div class="stat-val">${totalScore.toFixed(2)}/${scored.length}</div><div class="stat-label">总分</div></div>
    <div class="stat"><div class="stat-val">$${totalCost.toFixed(4)}</div><div class="stat-label">总费用</div></div>
    <div class="stat"><div class="stat-val">${(totalTokens/1000).toFixed(1)}K</div><div class="stat-label">总Tokens</div></div>
  </div>
  <div class="leaderboard-sort" style="margin-top:10px">
    <span class="leaderboard-meta">任务类别：</span>
    ${categoryButtons}
  </div>`;

  const cardsHtml = tasks.map(t => {
    const score = t.grading?.mean;
    const scoreStr = score !== undefined ? score.toFixed(2) : '—';
    const scoreClass = score === undefined ? '' : score >= 0.8 ? 'score-high' : score >= 0.4 ? 'score-mid' : 'score-low';
    const badge = t.status === 'success' ? 'success' : t.timed_out ? 'timeout' : t.status === 'error' ? 'error' : 'lowscore';
    const badgeText = t.status === 'success' ? '成功' : t.timed_out ? '超时' : t.status === 'error' ? '错误' : t.status;
    const execTime = t.execution_time ? `${t.execution_time.toFixed(1)}s` : '';
    const name = t.frontmatter?.name || t.task_id;
    const disabled = rerunJobForTask(t.task_id) ? 'disabled' : '';
    return `<div class="task-card" onclick="openTask('${t.task_id}')">
      <div class="tc-id">${t.task_id}</div>
      <div class="tc-name">${name}</div>
      <div>
        <span class="tc-score ${scoreClass}">${scoreStr}</span>
        <span class="tc-badge badge-${badge}" style="margin-left:8px">${badgeText}</span>
      </div>
      <div class="tc-meta">
        <span>${execTime}</span>
        <span>${t.usage?.total_tokens ? (t.usage.total_tokens/1000).toFixed(1)+'K tok' : ''}</span>
      </div>
      <div class="tc-actions">
        <button type="button" class="action-btn" ${disabled} onclick="rerunTask('${t.task_id}', event)">${rerunLabel(t.task_id)}</button>
      </div>
    </div>`;
  }).join('');

  document.getElementById('task-panel').innerHTML = summaryHtml + '<div class="section-title">任务列表</div><div id="task-grid">' + cardsHtml + '</div>';
}

// ---------------------------------------------------------------------------
// Task detail → Conversation view
// ---------------------------------------------------------------------------
async function openTask(taskId) {
  currentTaskId = taskId;
  currentTranscriptData = null;
  document.getElementById('task-panel').style.display = 'none';
  const detailPane = document.getElementById('detail-pane');
  detailPane.classList.add('open');
  document.getElementById('back-btn').style.display = 'inline-flex';

  // Find task data
  const task = (currentRunData?.tasks || []).find(t => t.task_id === taskId);

  // Header
  document.getElementById('oc-page-title').textContent = '聊天';
  document.getElementById('dh-id').textContent = taskId;
  document.getElementById('dh-name').textContent = task?.frontmatter?.name || taskId;
  const statsEl = document.getElementById('dh-stats');
  if (task) {
    const score = task.grading?.mean;
    const scoreStr = score !== undefined ? `${score.toFixed(2)} / ${task.grading?.max || 1}` : '—';
    const scoreClass = score === undefined ? '' : score >= 0.8 ? 'score-high' : score >= 0.4 ? 'score-mid' : 'score-low';
    statsEl.innerHTML = `
      <div class="dh-stat">评分 <span class="${scoreClass}">${scoreStr}</span></div>
      <div class="dh-stat">耗时 <span>${task.execution_time ? task.execution_time.toFixed(1)+'s' : '—'}</span></div>
      <div class="dh-stat">Tokens <span>${task.usage?.total_tokens?.toLocaleString() || '—'}</span></div>
      <div class="dh-stat">费用 <span>$${task.usage?.cost_usd?.toFixed(5) || '—'}</span></div>
      <div class="dh-stat">请求数 <span>${task.usage?.request_count || '—'}</span></div>
      <div class="dh-stat">类别 <span>${task.frontmatter?.category || '—'}</span></div>
    `;
  }
  renderDetailActions(task);

  // Grading panel
  renderGrading(task);

  const inputBar = document.getElementById('transcript-input-bar');
  if (inputBar) inputBar.style.display = 'flex';

  // Transcript
  document.getElementById('transcript-pane').innerHTML = '<div class="loading">加载对话...</div>';
  try {
    const transcript = await apiFetch(`/api/transcript/${currentRunId}/${taskId}`);
    currentTranscriptData = transcript;
    updatePillsForTask(task, transcript.meta || {});
    renderTranscript(transcript);
  } catch(e) {
    document.getElementById('transcript-pane').innerHTML = `<div class="loading">无对话记录: ${e.message}</div>`;
    renderArtifactStrip([]);
    updatePillsForTask(task, null);
  }
}

function showTaskGrid() {
  document.getElementById('task-panel').style.display = 'block';
  document.getElementById('detail-pane').classList.remove('open');
  document.getElementById('back-btn').style.display = 'none';
  const inputBar = document.getElementById('transcript-input-bar');
  if (inputBar) inputBar.style.display = 'none';
  document.getElementById('detail-body')?.classList.remove('detail-focus');
  currentTaskId = null;
  currentTranscriptData = null;
  document.getElementById('oc-page-title').textContent = '任务';
  if (currentRunData?.tasks) {
    setSubbarVisible(true);
    updatePillsForRun();
  } else {
    setSubbarVisible(false);
  }
}

// ---------------------------------------------------------------------------
// Grading panel
// ---------------------------------------------------------------------------
function renderGrading(task) {
  const el = document.getElementById('grading-pane');
  if (!task?.grading) { el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">无评分数据</div>'; return; }
  const g = task.grading;
  const score = g.mean ?? 0;
  const scoreClass = score >= 0.8 ? 'score-high' : score >= 0.4 ? 'score-mid' : 'score-low';

  // Breakdown from first run
  const run0 = g.runs?.[0] || {};
  const breakdown = run0.breakdown || {};
  const bRows = Object.entries(breakdown).map(([k, v]) => {
    const vc = v >= 0.8 ? 'score-high' : v > 0 ? 'score-mid' : 'score-low';
    return `<div class="gb-row"><span class="gb-key">${k}</span><span class="gb-val ${vc}">${typeof v === 'number' ? v.toFixed(2) : v}</span></div>`;
  }).join('');

  const notes = run0.notes ? `<div class="grading-notes">${escHtml(run0.notes)}</div>` : '';

  const usage = task.usage || {};
  const usageHtml = `<div class="usage-block">
    <h3>Token 使用</h3>
    <div class="grading-breakdown">
      <div class="gb-row"><span class="gb-key">输入</span><span class="gb-val">${(usage.input_tokens||0).toLocaleString()}</span></div>
      <div class="gb-row"><span class="gb-key">输出</span><span class="gb-val">${(usage.output_tokens||0).toLocaleString()}</span></div>
      <div class="gb-row"><span class="gb-key">缓存读</span><span class="gb-val">${(usage.cache_read_tokens||0).toLocaleString()}</span></div>
      <div class="gb-row"><span class="gb-key">缓存写</span><span class="gb-val">${(usage.cache_write_tokens||0).toLocaleString()}</span></div>
      <div class="gb-row"><span class="gb-key">合计</span><span class="gb-val">${(usage.total_tokens||0).toLocaleString()}</span></div>
      <div class="gb-row"><span class="gb-key">费用</span><span class="gb-val">$${(usage.cost_usd||0).toFixed(5)}</span></div>
    </div>
  </div>`;

  el.innerHTML = `
    <h3>评分详情</h3>
    <div class="grading-score-big ${scoreClass}">${score.toFixed(2)}<span style="font-size:1rem;color:var(--muted)"> / ${g.max || 1}</span></div>
    <div style="font-size:0.75rem;color:var(--muted);margin-bottom:8px">类型: ${run0.grading_type || '—'}</div>
    <div class="grading-breakdown">${bRows}</div>
    ${notes}
    ${usageHtml}
  `;
}

// ---------------------------------------------------------------------------
// Markdown setup (marked + highlight.js)
// ---------------------------------------------------------------------------
function setupMarked() {
  const markedLib = window.marked;
  if (!markedLib) return false;
  const renderer = new markedLib.Renderer();

  // Code blocks: wrap with header (lang + copy button) + highlight.js
  renderer.code = (...args) => {
    const { text, lang } = normalizeMarkedCodeArgs(args);
    let highlighted = escHtml(text);
    if (typeof hljs !== 'undefined') {
      try {
        highlighted = lang && hljs.getLanguage(lang)
          ? hljs.highlight(text, { language: lang }).value
          : hljs.highlightAuto(text).value;
      } catch(e) {}
    }
    const langBadge = lang ? `<span class="code-block-lang">${escHtml(lang)}</span>` : '';
    const escapedCode = text.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const copyBtn = `<button class="code-block-copy" data-copy="${escapedCode}" onclick="copyBtn(this)">Copy</button>`;
    return `<div class="code-block-wrapper">
      <div class="code-block-header">${langBadge}${copyBtn}</div>
      <pre><code class="hljs${lang ? ' language-'+escHtml(lang) : ''}">${highlighted}</code></pre>
    </div>`;
  };

  // Inline code
  renderer.codespan = (...args) => {
    const text = normalizeMarkedInlineCodeArgs(args);
    return `<code>${escHtml(text)}</code>`;
  };

  // Never trust inline HTML from transcript content.
  renderer.html = (...args) => {
    const first = args[0];
    const raw = (first && typeof first === 'object')
      ? String(first.text || first.raw || '')
      : String(first || '');
    return escHtml(raw);
  };

  markedLib.setOptions({ renderer, gfm: true, breaks: true });
  return true;
}

function renderMarkdown(text) {
  if (!text?.trim()) return '';
  const markedLib = window.marked;
  if (!markedLib) return `<pre style="white-space:pre-wrap">${escHtml(text)}</pre>`;
  try { return markedLib.parse(text); }
  catch(e) { return `<pre style="white-space:pre-wrap">${escHtml(text)}</pre>`; }
}

function copyBtn(btn) {
  const text = btn.dataset.copy;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1500);
  });
}

// ---------------------------------------------------------------------------
// 文件输出弹窗预览（read / 结构化 path+content / write 参数）
// ---------------------------------------------------------------------------
const __fpStore = {};
let __fpSeq = 0;

function resetFilePreviewStore() {
  Object.keys(__fpStore).forEach(k => { delete __fpStore[k]; });
  __fpSeq = 0;
}

function registerFilePreview(payload) {
  const id = 'fp' + (++__fpSeq);
  __fpStore[id] = payload;
  return id;
}

function inferFileKindFromPath(path, content) {
  const ext = (path || '').split('.').pop()?.toLowerCase() || '';
  const c = String(content || '').trim();
  if (['png','jpg','jpeg','gif','webp','bmp','ico'].includes(ext)) return 'image';
  if (ext === 'svg') return 'image-svg';
  if (c.startsWith('data:image/')) return 'image';
  if (ext === 'md' || ext === 'markdown') return 'markdown';
  if (ext === 'json' || ext === 'jsonl') return 'json';
  if (ext === 'csv' || ext === 'tsv') return 'csv';
  if (ext === 'html' || ext === 'htm') return 'html';
  if (['py','js','ts','tsx','jsx','rs','go','java','c','cpp','h','css','sh','bash','yaml','yml','toml','sql','vue','svelte'].includes(ext)) return 'code';
  if (c.startsWith('{') || c.startsWith('[')) {
    try { JSON.parse(c); return 'json'; } catch (e) {}
  }
  if (c.includes(',') && c.includes('\n') && c.split('\n').length >= 2) return 'csv';
  return 'text';
}

function guessMimeFromFilename(name) {
  const ext = String(name || '').split('.').pop()?.toLowerCase() || '';
  const map = {
    png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', gif: 'image/gif', webp: 'image/webp',
    svg: 'image/svg+xml', md: 'text/markdown', json: 'application/json', csv: 'text/csv',
    html: 'text/html', htm: 'text/html', txt: 'text/plain', py: 'text/x-python', js: 'text/javascript',
    ts: 'text/typescript', css: 'text/css', yaml: 'text/yaml', yml: 'text/yaml'
  };
  return map[ext] || 'application/octet-stream';
}

function triggerDownloadPayload(p) {
  if (!p) return;
  const name = String((p.path || p.title || 'download').split('/').pop() || 'download');
  if (p.kind === 'image-url' && p.imageUrl) {
    const a = document.createElement('a');
    a.href = p.imageUrl;
    a.target = '_blank';
    a.rel = 'noreferrer';
    a.download = name;
    a.click();
    return;
  }
  if (p.isBase64 && typeof p.content === 'string') {
    try {
      const bin = atob(p.content.replace(/\s/g, ''));
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      const mime = p.mime || guessMimeFromFilename(name);
      const blob = new Blob([bytes], { type: mime });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    } catch (e) {
      console.error(e);
    }
    return;
  }
  const text = String(p.content ?? '');
  const mime = guessMimeFromFilename(name);
  const blob = new Blob([text], { type: mime + ';charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

function renderCsvTable(csv) {
  const lines = String(csv || '').trim().split(/\r?\n/).filter(Boolean);
  if (!lines.length) return `<pre class="file-modal-pre">${escHtml(csv)}</pre>`;
  const parseRow = (line) => {
    const out = []; let cur = ''; let q = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') { q = !q; continue; }
      if (!q && ch === ',') { out.push(cur); cur = ''; continue; }
      cur += ch;
    }
    out.push(cur);
    return out.map(s => s.trim());
  };
  const rows = lines.map(parseRow);
  const maxCols = Math.max(0, ...rows.map(r => r.length));
  const head = rows[0] || [];
  const rest = rows.slice(1, 401);
  const th = head.map(c => `<th>${escHtml(c)}</th>`).join('');
  const tb = rest.map(r => {
    const cells = [...r];
    while (cells.length < maxCols) cells.push('');
    return '<tr>' + cells.slice(0, maxCols).map(c => `<td>${escHtml(c)}</td>`).join('') + '</tr>';
  }).join('');
  const more = rows.length > 401 ? `<p class="result-card-meta" style="padding:8px">仅显示前 400 行</p>` : '';
  return `<div class="file-modal-table-wrap"><table class="file-modal-csv"><thead><tr>${th}</tr></thead><tbody>${tb}</tbody></table>${more}</div>`;
}

function buildFilePreviewFromResult(turn, tcOpt, raw, parsed) {
  const name = (turn.tool_name || tcOpt?.name || '').toLowerCase();
  const pathArg = tcOpt?.arguments?.path || tcOpt?.arguments?.file || tcOpt?.arguments?.target_path || '';

  if (name === 'read' && raw && raw.trim()) {
    if (parsed === null) {
      return { title: pathArg || 'read', path: pathArg, content: raw, kind: inferFileKindFromPath(pathArg, raw), sub: 'read 工具输出（文本）' };
    }
    const body = parsed.text ?? parsed.content ?? parsed.body ?? parsed.data;
    if (typeof body === 'string' && body.length) {
      const fp = parsed.path || pathArg;
      return { title: fp || 'read', path: fp, content: body, kind: inferFileKindFromPath(String(fp || ''), body), sub: 'read 工具输出' };
    }
    return { title: pathArg || 'read.json', path: pathArg, content: JSON.stringify(parsed, null, 2), kind: 'json', sub: 'read 工具输出（JSON）' };
  }

  if (parsed && typeof parsed === 'object') {
    const p = parsed.path || parsed.filePath || parsed.file;
    const body = parsed.text ?? parsed.content ?? parsed.body;
    if (typeof p === 'string' && typeof body === 'string' && body.length) {
      return { title: p, path: p, content: body, kind: inferFileKindFromPath(p, body), sub: '工具返回中的文件内容' };
    }
  }

  return null;
}

function buildWritePreviewPayload(tc) {
  const n = (tc.name || '').toLowerCase();
  if (n !== 'write') return null;
  const args = tc.arguments || {};
  const path = args.path || args.target || '';
  const content = args.content;
  if (typeof content !== 'string' || !content.length) return null;
  return {
    title: path || 'write',
    path,
    content,
    kind: inferFileKindFromPath(path, content),
    sub: 'write 写入内容（来自工具参数）'
  };
}

/** 匹配命令行 / 输出中的文件路径，便于点击打开（依赖对话内 read/write 索引） */
const FILE_PATH_RE = /\b(?:\.\/)?(?:[\w.\-]+\/)*[\w.\-]+\.(?:md|markdown|json|csv|py|ts|tsx|js|jsx|html|htm|txt|yaml|yml|sh|bash|rs|go|toml)\b/gi;

function buildTranscriptFileIndex(turns, resultByCallId) {
  const index = Object.create(null);
  function addKey(path, payload) {
    if (!path || typeof path !== 'string') return;
    const p = path.trim();
    const base = p.split('/').pop();
    const noDot = p.replace(/^\.\//, '');
    [p, base, noDot].forEach(k => { if (k) index[k] = payload; });
  }

  turns.forEach(turn => {
    if (turn.role !== 'assistant') return;
    const toolCalls = turn.parts.filter(p => p.type === 'toolCall');
    for (const tc of toolCalls) {
      const name = (tc.name || '').toLowerCase();
      const args = tc.arguments || {};
      if (name === 'write' && typeof args.content === 'string' && args.content.length && args.path) {
        addKey(args.path, {
          content: args.content,
          path: args.path,
          from: 'write',
          kind: inferFileKindFromPath(args.path, args.content)
        });
      }
      if (name === 'read' && args.path) {
        const rt = tc.id ? resultByCallId[tc.id] : null;
        if (!rt) continue;
        const raw = rt.parts.map(p => p.text || '').join('');
        let body = raw;
        let parsed = null;
        try {
          parsed = JSON.parse(raw);
          if (parsed && typeof parsed === 'object') {
            const b = parsed.text ?? parsed.content ?? parsed.body ?? parsed.data;
            if (typeof b === 'string') body = b;
            else body = JSON.stringify(parsed, null, 2);
          }
        } catch (e) { /* 纯文本 */ }
        addKey(args.path, {
          content: body,
          path: args.path,
          from: 'read',
          kind: inferFileKindFromPath(args.path, body)
        });
      }
    }
  });
  return index;
}

function linkifyPathsInPlainText(text) {
  if (!text) return '';
  const re = new RegExp(FILE_PATH_RE.source, FILE_PATH_RE.flags);
  let out = '';
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    out += escHtml(text.slice(last, m.index));
    const fn = m[0];
    out += `<button type="button" class="path-link" data-file="${escapeAttr(fn)}">${escHtml(fn)}</button>`;
    last = m.index + m[0].length;
  }
  out += escHtml(text.slice(last));
  return out;
}

function linkifyFilePathsInTranscript(root) {
  if (!root) return;
  const re = new RegExp(FILE_PATH_RE.source, FILE_PATH_RE.flags);
  const sel = '.arg-preview, .result-inline-text, .toolcall-block .tc-arg-val, .tc-arg pre code, .result-body pre code, details.result-block > summary .result-preview';
  root.querySelectorAll(sel).forEach(el => {
    const t = el.textContent;
    if (!t || t.length > 800000) return;
    re.lastIndex = 0;
    if (!re.test(t)) return;
    re.lastIndex = 0;
    el.innerHTML = linkifyPathsInPlainText(t);
  });
}

function openFileFromTranscriptIndex(filename) {
  const idx = window.__transcriptFileIndex || {};
  const raw = String(filename || '').trim();
  let hit = idx[raw];
  if (!hit) hit = idx[raw.split('/').pop()];
  if (!hit) {
    const base = raw.replace(/^\.\//, '');
    hit = idx[base];
  }
  if (hit) {
    openFilePreviewById(registerFilePreview({
      title: hit.path || raw,
      path: hit.path,
      content: hit.content,
      kind: hit.kind || inferFileKindFromPath(hit.path, hit.content),
      sub: hit.from === 'read' ? '来自本对话中的 read 输出' : '来自本对话中的 write 参数'
    }));
    return;
  }
  openFilePreviewById(registerFilePreview({
    title: raw,
    content: '未在对话记录中找到该文件的正文。请确认此前已通过 read 读取该文件，或 write 写入过该路径；点击的文件名需与记录一致（含后缀）。若仅有 exec/wc 等命令引用文件名，需先有 read 才会显示内容。',
    kind: 'text',
    sub: '提示'
  }));
}

/** 汇总本次对话中的输出文件（write/read + 工具返回的图片等），供底部条展示 */
function collectOutputArtifacts(turns, resultByCallId) {
  const map = new Map();
  const order = [];
  function touch(path, art) {
    const k = String(path || '').trim();
    if (!k) return;
    if (!map.has(k)) order.push(k);
    map.set(k, art);
  }

  turns.forEach(turn => {
    if (turn.role !== 'assistant') return;
    const toolCalls = turn.parts.filter(p => p.type === 'toolCall');
    for (const tc of toolCalls) {
      const name = (tc.name || '').toLowerCase();
      const args = tc.arguments || {};
      if (name === 'write' && args.path && typeof args.content === 'string' && args.content.length) {
        const path = args.path;
        touch(path, {
          path,
          content: args.content,
          from: 'write',
          kind: inferFileKindFromPath(path, args.content)
        });
      }
      if (name === 'read' && args.path) {
        const rt = tc.id ? resultByCallId[tc.id] : null;
        if (!rt) continue;
        const raw = rt.parts.map(p => p.text || '').join('');
        let body = raw;
        try {
          const p = JSON.parse(raw);
          if (p && typeof p === 'object') {
            const b = p.text ?? p.content ?? p.body ?? p.data;
            if (typeof b === 'string') body = b;
            else body = JSON.stringify(p, null, 2);
          }
        } catch (e) {}
        touch(args.path, {
          path: args.path,
          content: body,
          from: 'read',
          kind: inferFileKindFromPath(args.path, body)
        });
      }
    }
  });

  let extra = 0;
  turns.forEach(turn => {
    if (turn.role !== 'toolResult') return;
    const raw = turn.parts.map(p => p.text || '').join('');
    try {
      const p = JSON.parse(raw);
      if (!p || typeof p !== 'object') return;
      if (typeof p.image === 'string' && p.image.startsWith('data:')) {
        const m = p.image.match(/^data:([^;]+);base64,(.+)$/);
        if (m) {
          touch('::__tool_img_' + (extra++) + '__', {
            path: 'image.png',
            title: 'image (tool)',
            content: m[2],
            from: 'tool',
            kind: 'image-b64',
            isBase64: true,
            mime: m[1]
          });
        }
      }
      if (typeof p.url === 'string' && /\.(png|jpe?g|gif|webp)(\?|#|$)/i.test(p.url)) {
        const fn = p.url.split('/').pop().split('?')[0] || 'image';
        touch('::__tool_url_' + (extra++) + '__', {
          path: fn,
          content: '',
          from: 'url',
          kind: 'image-url',
          imageUrl: p.url
        });
      }
    } catch (e) {}
  });

  return order.map(k => map.get(k)).filter(Boolean);
}

function renderArtifactStrip(artifacts) {
  const bar = document.getElementById('transcript-artifacts');
  const strip = document.getElementById('ta-strip');
  if (!bar || !strip) return;
  if (!artifacts || !artifacts.length) {
    bar.classList.add('is-empty');
    strip.innerHTML = '';
    return;
  }
  bar.classList.remove('is-empty');
  strip.innerHTML = artifacts.map((art) => {
    const payload = Object.assign({}, art);
    const fid = registerFilePreview(payload);
    const base = String(art.path || art.title || 'file').split('/').pop();
    const fromLabel = art.from === 'write' ? '写入' : art.from === 'read' ? '读取' : art.from === 'url' ? '链接' : '工具';
    const k = art.kind || '';
    let ico = '📄';
    if (k === 'image-url' && art.imageUrl) ico = '🔗';
    else if (k === 'image' || k === 'image-b64' || k === 'image-svg') ico = '🖼';
    return `<div class="ta-card" role="button" tabindex="0" data-fp-open="${escHtml(fid)}" title="${escHtml(base)}">
      <span class="ta-ico" aria-hidden="true">${ico}</span>
      <div class="ta-body"><div class="ta-name">${escHtml(base)}</div><div class="ta-from">${escHtml(fromLabel)}</div></div>
    </div>`;
  }).join('');

  strip.querySelectorAll('.ta-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.getAttribute('data-fp-open');
      if (id) openFilePreviewById(id);
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); card.click(); }
    });
  });
}

// ---------------------------------------------------------------------------
// Transcript renderer — OpenClaw-style chat (staggered user / tool chips)
// Groups: user → [step: chips + expandable detail]* → final response
// ---------------------------------------------------------------------------
/** 剥离消息开头的 [Sun 2026-04-12 14:11 UTC] 一类时间戳（与后端 _split_user_bracket_prefix 一致） */
function splitUserLeadingTimestamp(text) {
  const t = String(text || '').replace(/^\uFEFF/, '');
  const m = t.match(/^\s*\[([^\]]+)\]\s*/);
  if (m) return { bracket: m[1], body: t.slice(m[0].length) };
  return { bracket: null, body: t };
}

/** 括号内 "Sun 2026-04-12 13:26 UTC" 等：提取 YYYY-MM-DD HH:mm 按 UTC 解析（避免 Date.parse 实现差异） */
function parseBracketTimeString(bracketInner) {
  if (!bracketInner || typeof bracketInner !== 'string') return null;
  const m = bracketInner.match(/(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
  if (m) {
    const d = new Date(Date.UTC(
      parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10),
      parseInt(m[4], 10), parseInt(m[5], 10), 0, 0
    ));
    if (!isNaN(d.getTime())) return d;
  }
  const d2 = new Date(bracketInner);
  return !isNaN(d2.getTime()) ? d2 : null;
}

function normalizeTurnTimestampToDate(ts) {
  if (ts == null || ts === undefined) return null;
  if (typeof ts === 'number') {
    const ms = ts > 1e12 ? ts : ts * 1000;
    const d = new Date(ms);
    return isNaN(d.getTime()) ? null : d;
  }
  const d = new Date(ts);
  return isNaN(d.getTime()) ? null : d;
}

/** 用户消息时间：固定用 UTC 展示，与 jsonl 中 [… UTC] / message.timestamp 一致，避免本地时区误读 */
const _userUtcOpts = {
  weekday: 'short',
  year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hour12: false,
  timeZone: 'UTC',
  timeZoneName: 'short'
};

/** 优先 message.timestamp（毫秒）；其次括号内文案；最后事件级 timestamp */
function formatUserTimeLabel(bracketInner, timestampMs, eventTs) {
  if (timestampMs != null && timestampMs !== undefined) {
    const d = new Date(Number(timestampMs));
    if (!isNaN(d.getTime())) {
      return { label: d.toLocaleString('zh-CN', _userUtcOpts), iso: d.toISOString() };
    }
  }
  if (bracketInner) {
    const d = parseBracketTimeString(bracketInner);
    if (d) {
      return { label: d.toLocaleString('zh-CN', _userUtcOpts), iso: d.toISOString() };
    }
    return { label: bracketInner, iso: '' };
  }
  const d = normalizeTurnTimestampToDate(eventTs);
  if (d) {
    return { label: d.toLocaleString('zh-CN', _userUtcOpts), iso: d.toISOString() };
  }
  return null;
}

function renderUserMessageHtml(turn) {
  const text = turn.parts.map(p => p.text || '').join('');
  const hasServer = turn.user_body_text !== undefined || turn.user_time_bracket !== undefined;
  let bracket;
  let body;
  if (hasServer) {
    bracket = turn.user_time_bracket != null ? turn.user_time_bracket : null;
    body = turn.user_body_text !== undefined ? String(turn.user_body_text) : splitUserLeadingTimestamp(text).body;
  } else {
    const sp = splitUserLeadingTimestamp(text);
    bracket = sp.bracket;
    body = sp.body;
  }
  // 未重启 viewer 时 API 仍返回整段 text：再剥一层，避免 [Sun … UTC] 留在气泡内
  const again = splitUserLeadingTimestamp(body);
  if (again.bracket) {
    bracket = bracket || again.bracket;
    body = again.body;
  }
  const timeInfo = formatUserTimeLabel(bracket, turn.timestamp_ms, turn.timestamp);
  const raw = body || '';
  const mdHtml = raw.trim()
    ? renderMarkdown(raw)
    : '<p style="margin:0;color:var(--muted)">（空消息）</p>';
  const wrapped = `<div class="response-md oc-user-md">${mdHtml}</div>`;
  let timeRow = '';
  if (timeInfo) {
    const dt = timeInfo.iso ? ` datetime="${escHtml(timeInfo.iso)}"` : '';
    timeRow = `<div class="oc-user-time-row"><time class="oc-user-time"${dt}>${escHtml(timeInfo.label)}</time></div>`;
  }
  return `${timeRow}<div class="oc-user-bubble">${wrapped}</div>`;
}

function renderOcChip(kind, toolName) {
  const bolt = kind === 'output' ? 'oc-chip-output' : '';
  const label = kind === 'output' ? 'Tool output' : 'Tool call';
  return `<div class="oc-chip ${bolt}"><span class="oc-chip-bolt">⚡</span><span>${label}</span> <code class="oc-chip-name">${escHtml(toolName || 'tool')}</code></div>`;
}

function renderTranscript(data) {
  const turns = data?.turns || [];
  const el = document.getElementById('transcript-pane');
  if (!turns.length) {
    el.innerHTML = '<div class="loading">对话为空</div>';
    renderArtifactStrip([]);
    return;
  }
  resetFilePreviewStore();

  // Build map: toolCallId → toolResult turn
  const resultByCallId = {};
  turns.forEach((t, i) => {
    if (t.role === 'toolResult') {
      if (t.tool_call_id) resultByCallId[t.tool_call_id] = t;
    }
  });
  window.__transcriptFileIndex = buildTranscriptFileIndex(turns, resultByCallId);

  const html = [];
  let stepNum = 0;
  const consumed = new Set();

  turns.forEach((turn, idx) => {
    if (turn.role === 'user') {
      const text = turn.parts.map(p => p.text || '').join('');
      if (!text.trim()) return;
      html.push(`<div class="oc-row oc-row-user">
        <div class="oc-user-wrap">
          ${renderUserMessageHtml(turn)}
          <div class="oc-user-meta"><span>You</span><span class="oc-del">🗑</span></div>
        </div>
        <div class="oc-avatar" title="User">🙂</div>
      </div>`);

    } else if (turn.role === 'assistant') {
      const thinking  = turn.parts.filter(p => p.type === 'thinking');
      const toolCalls = turn.parts.filter(p => p.type === 'toolCall');
      const texts     = turn.parts.filter(p => p.type === 'text' && p.text?.trim());

      if (toolCalls.length > 0) {
        stepNum++;
        const thinkingHtml = thinking.map(renderThinkingBlock).join('');
        const toolList = Array.from(new Set(toolCalls.map(tc => tc.name || 'tool')));
        const toolsLabel = toolList.join(', ');
        const thoughtPreview = thinking.length
          ? truncateText(thinking.map(t => t.text || '').join(' '), 140)
          : '无思考片段';

        const pairs = [];
        toolCalls.forEach(tc => {
          let resultTurn = tc.id ? resultByCallId[tc.id] : null;
          if (!resultTurn) {
            for (let j = idx + 1; j < turns.length; j++) {
              if (turns[j].role === 'toolResult' && !consumed.has(j)) {
                resultTurn = turns[j]; consumed.add(j); break;
              }
              if (turns[j].role === 'assistant') break;
            }
          }
          pairs.push({ tc, resultTurn });
        });

        const chipsParts = pairs.map(({ tc, resultTurn }) => {
          let s = renderOcChip('call', tc.name);
          if (resultTurn) s += renderOcChip('output', resultTurn.tool_name || tc.name);
          return s;
        });

        const toolBlocksHtml = pairs.map(({ tc, resultTurn }) =>
          renderToolCallBlock(tc) + (resultTurn ? renderResultBlock(resultTurn, tc) : '')
        ).join('');
        const fallbackHtml = toolBlocksHtml ? '' : '<div class="step-empty">该步骤没有可展示的工具参数或结果。</div>';
        const followupTextHtml = texts.length
          ? `<div class="step-followup">${texts.map(p => `<div class="response-md">${renderMarkdown(p.text)}</div>`).join('')}</div>`
          : '';
        const metaHtml = `<div class="step-meta">
          <span class="step-tools">🛠 ${escHtml(toolsLabel || 'tool')}</span>
          <span class="step-hint">${escHtml(thoughtPreview)}</span>
        </div>`;

        html.push(`<div class="oc-row oc-row-assistant">
          <div class="oc-assistant-wrap">
            <div class="oc-chips">${chipsParts.join('')}</div>
            <details class="oc-step-expand">
              <summary><span class="oc-step-arrow">▶</span> 展开详情 · 步骤 ${stepNum} · ${escHtml(toolsLabel)}</summary>
              <div class="oc-step-inner">
                <div class="parts">${metaHtml}${thinkingHtml}${toolBlocksHtml}${fallbackHtml}${followupTextHtml}</div>
              </div>
            </details>
          </div>
        </div>`);

      } else if (texts.length > 0 || thinking.length > 0) {
        const thinkingHtml = thinking.map(renderThinkingBlock).join('');
        const textsHtml = texts.map(p =>
          `<div class="response-md">${renderMarkdown(p.text)}</div>`
        ).join('');
        html.push(`<div class="oc-row oc-row-assistant">
          <div class="oc-final-bubble">
            ${thinkingHtml}${textsHtml}
          </div>
        </div>`);
      }
    }
    // toolResult turns rendered inline; skip orphans
  });

  el.innerHTML = '<div class="oc-chat">' + html.join('') + '</div>';

  // Apply highlight.js to any un-highlighted code blocks
  if (typeof hljs !== 'undefined') {
    el.querySelectorAll('pre code:not(.hljs)').forEach(block => hljs.highlightElement(block));
  }
  linkifyFilePathsInTranscript(el);
  const artifacts = collectOutputArtifacts(turns, resultByCallId);
  renderArtifactStrip(artifacts);
  setupTranscriptScroll();
}

function normalizeMarkedCodeArgs(args) {
  const first = args[0];
  if (first && typeof first === 'object') {
    return {
      text: String(first.text || ''),
      lang: String(first.lang || '')
    };
  }
  return {
    text: String(first || ''),
    lang: String(args[1] || '').trim().split(/\s+/)[0]
  };
}

function normalizeMarkedInlineCodeArgs(args) {
  const first = args[0];
  if (first && typeof first === 'object') return String(first.text || '');
  return String(first || '');
}

function renderThinkingBlock(p) {
  if (!p.text?.trim()) return '';
  const preview = p.text.replace(/\s+/g, ' ').slice(0, 120) + (p.text.length > 120 ? '…' : '');
  return `<details class="thinking-block">
    <summary>
      <span class="arrow">▶</span>
      <span>💭 思考过程</span>
      <span class="th-preview">${escHtml(preview)}</span>
    </summary>
    <div class="thinking-body">${escHtml(p.text)}</div>
  </details>`;
}

// Guess language for a long string value based on key name and content
function guessArgLang(key, val) {
  if (key === 'command' || key === 'script' || key === 'cmd') return 'bash';
  if (key === 'query' && !val.trim().startsWith('{')) return 'sql';
  const t = val.trim();
  if (t.startsWith('{') || t.startsWith('[')) return 'json';
  if (t.startsWith('<')) return 'xml';
  if (key === 'content' || key === 'text' || key === 'body' || key === 'message') {
    if (t.includes('# ') || t.includes('**') || t.includes('- [')) return 'markdown';
    if (t.includes('def ') || t.includes('import ')) return 'python';
  }
  return 'plaintext';
}

function truncateText(text, maxLen = 180) {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim();
  if (normalized.length <= maxLen) return normalized;
  return normalized.slice(0, maxLen) + '…';
}

function truncateMultiline(text, maxLen = 1200) {
  const source = String(text || '').trim();
  if (source.length <= maxLen) return source;
  return source.slice(0, maxLen) + '\n…(已截断)';
}

function cleanExternalContent(text) {
  return String(text || '')
    .replace(/<<<EXTERNAL_UNTRUSTED_CONTENT[^>]*>>>/g, '')
    .replace(/<<<END_EXTERNAL_UNTRUSTED_CONTENT[^>]*>>>/g, '')
    .replace(/^Source:\s.*$/gm, '')
    .replace(/^\s*---\s*$/gm, '')
    .replace(/^SECURITY NOTICE:[\s\S]*?(?=\n\n|\n\[|$)/m, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function escapeAttr(s) {
  return escHtml(String(s || '')).replace(/\n/g, '&#10;');
}

function renderHighlightedBlock(text, lang = 'plaintext', maxHeight = 320) {
  const source = String(text || '');
  let highlighted = escHtml(source);
  if (typeof hljs !== 'undefined') {
    try {
      highlighted = lang && hljs.getLanguage && hljs.getLanguage(lang)
        ? hljs.highlight(source, { language: lang }).value
        : hljs.highlightAuto(source).value;
    } catch(e) {}
  }
  return `<pre style="max-height:${maxHeight}px"><code class="hljs language-${escHtml(lang)}">${highlighted}</code></pre>`;
}

function renderFilePreviewContent(p) {
  const kind = p.kind || 'text';
  const content = String(p.content ?? '');
  if (kind === 'image-url' && p.imageUrl) {
    return `<div class="file-modal-img-wrap"><img class="file-modal-img" alt="" src="${escapeAttr(p.imageUrl)}" /></div>`;
  }
  if (kind === 'image-b64' || (kind === 'image' && p.isBase64)) {
    const mime = p.mime || guessMimeFromFilename(p.path || 'image.png') || 'image/png';
    const src = `data:${mime};base64,${String(p.content).replace(/\s/g, '')}`;
    return `<div class="file-modal-img-wrap"><img class="file-modal-img" alt="" src="${escapeAttr(src)}" /></div>`;
  }
  if (kind === 'image-svg') {
    const src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(content);
    return `<div class="file-modal-img-wrap"><img class="file-modal-img" alt="" src="${escapeAttr(src)}" /></div>`;
  }
  if (kind === 'image') {
    if (content.startsWith('data:image')) {
      return `<div class="file-modal-img-wrap"><img class="file-modal-img" alt="" src="${escapeAttr(content)}" /></div>`;
    }
    return `<p class="result-card-meta" style="margin-bottom:10px">该条目为图片类型；若正文为二进制，请使用「下载」保存后本地打开。</p><pre class="file-modal-pre">${escHtml(content.slice(0, 4000))}${content.length > 4000 ? '…' : ''}</pre>`;
  }
  if (kind === 'markdown') {
    const html = (typeof window.marked !== 'undefined' && window.marked)
      ? renderMarkdown(content)
      : `<pre class="file-modal-pre">${escHtml(content)}</pre>`;
    return `<div class="file-modal-md response-md">${html}</div>`;
  }
  if (kind === 'json') {
    let pretty = content;
    try { pretty = JSON.stringify(JSON.parse(content), null, 2); } catch (e) {}
    return renderHighlightedBlock(pretty, 'json', 560);
  }
  if (kind === 'csv') {
    return renderCsvTable(content);
  }
  if (kind === 'html') {
    return `<p class="result-card-meta" style="margin-bottom:10px">HTML 源码（转义展示）</p>` + renderHighlightedBlock(content, 'xml', 560);
  }
  if (kind === 'code') {
    const ext = (p.path || p.title || '').split('.').pop()?.toLowerCase() || '';
    const map = { py: 'python', js: 'javascript', ts: 'typescript', tsx: 'typescript', jsx: 'javascript', rs: 'rust', go: 'go', sh: 'bash', yaml: 'yaml', yml: 'yaml', vue: 'xml', css: 'css', sql: 'sql' };
    const hl = map[ext] || 'plaintext';
    return renderHighlightedBlock(content, hl, 560);
  }
  return `<pre class="file-modal-pre"><code>${escHtml(content)}</code></pre>`;
}

function openFilePreviewById(id) {
  const p = __fpStore[id];
  if (!p) return;
  window.__lastFpId = id;
  const titleEl = document.getElementById('file-modal-title');
  const subEl = document.getElementById('file-modal-sub');
  const bodyEl = document.getElementById('file-modal-body');
  const modal = document.getElementById('file-preview-modal');
  const dlBtn = document.getElementById('file-modal-download');
  if (!titleEl || !bodyEl || !modal) return;
  titleEl.textContent = p.title || p.path || '文件预览';
  if (subEl) subEl.textContent = p.sub || (p.path ? String(p.path) : '');
  bodyEl.innerHTML = renderFilePreviewContent(p);
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  if (typeof hljs !== 'undefined') {
    bodyEl.querySelectorAll('pre code').forEach(block => {
      try { hljs.highlightElement(block); } catch (e) {}
    });
  }
  if (dlBtn) {
    const canDl = !!(p.kind === 'image-url' && p.imageUrl) || !!p.isBase64
      || (typeof p.content === 'string' && p.content.length > 0);
    dlBtn.style.display = canDl ? 'inline-block' : 'none';
    dlBtn.onclick = () => triggerDownloadPayload(p);
  }
}

function closeFilePreviewModal() {
  const modal = document.getElementById('file-preview-modal');
  if (!modal) return;
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
}

function setupFilePreviewModal() {
  const modal = document.getElementById('file-preview-modal');
  const backdrop = document.getElementById('file-modal-backdrop');
  const closeBtn = document.getElementById('file-modal-close');
  backdrop?.addEventListener('click', closeFilePreviewModal);
  closeBtn?.addEventListener('click', closeFilePreviewModal);
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal?.classList.contains('open')) closeFilePreviewModal();
  });
}

function renderResultMetaGrid(parsed) {
  const preferredKeys = ['query', 'url', 'finalUrl', 'status', 'count', 'tookMs', 'durationMs', 'exitCode', 'cwd', 'contentType', 'length'];
  const rows = preferredKeys
    .filter(key => parsed[key] !== undefined && parsed[key] !== null && typeof parsed[key] !== 'object')
    .map(key => `<div class="result-kv"><div class="result-kv-key">${escHtml(key)}</div><div class="result-kv-val">${escHtml(String(parsed[key]))}</div></div>`);
  if (!rows.length) return '';
  return `<div class="result-kv-grid">${rows.join('')}</div>`;
}

function renderSearchResults(results) {
  const items = (results || []).slice(0, 6).map(item => {
    const title = cleanExternalContent(item.title || 'Untitled result');
    const description = cleanExternalContent(item.description || '');
    const meta = [item.siteName, item.published].filter(Boolean).join(' · ');
    const titleHtml = item.url
      ? `<a href="${escHtml(item.url)}" target="_blank" rel="noreferrer">${escHtml(title)}</a>`
      : escHtml(title);
    return `<div class="result-card">
      <div class="result-card-title">${titleHtml}</div>
      ${meta ? `<div class="result-card-meta">${escHtml(meta)}</div>` : ''}
      ${description ? `<div class="result-card-desc">${escHtml(description)}</div>` : ''}
    </div>`;
  }).join('');

  const moreCount = Math.max(0, (results || []).length - 6);
  const moreHtml = moreCount ? `<div class="result-card-meta">还有 ${moreCount} 条结果未展开</div>` : '';
  return items ? `<div class="result-list">${items}${moreHtml}</div>` : '';
}

function renderToolTextPreview(text, lang) {
  if (!text?.trim()) return '';
  const cleaned = cleanExternalContent(text);
  const preview = lang === 'markdown'
    ? truncateMultiline(cleaned, 900)
    : truncateMultiline(cleaned, 600);
  return `<div class="arg-preview">${escHtml(preview)}</div>`;
}

function renderToolCallBlock(tc) {
  const args = tc.arguments || {};
  const fullJson = JSON.stringify(args, null, 2);
  const wp = buildWritePreviewPayload(tc);
  let writePreviewBtn = '';
  if (wp) {
    const wid = registerFilePreview(wp);
    writePreviewBtn = `<button type="button" class="file-preview-btn file-preview-btn-sm" onclick="event.stopPropagation(); openFilePreviewById('${wid}')">弹窗查看写入</button>`;
  }

  let argsHtml = '';
  for (const [key, val] of Object.entries(args)) {
    const keyHtml = `<div class="tc-arg-key">${escHtml(key)}</div>`;

    if (typeof val === 'string' && (val.includes('\n') || val.length > 120)) {
      // Long / multiline string: show raw content (not JSON-escaped) in expandable block
      const lang = guessArgLang(key, val);
      const lines = val.split('\n').length;
      argsHtml += `<div class="tc-arg">${keyHtml}
        ${renderToolTextPreview(val, lang)}
        <details class="tc-arg-long" open>
          <summary><span class="arrow">▶</span>${lines} 行 · ${val.length} 字符 · ${lang}</summary>
          ${renderHighlightedBlock(val, lang, 360)}
        </details>
      </div>`;
    } else if (typeof val === 'object' && val !== null) {
      const jsonStr = JSON.stringify(val, null, 2);
      argsHtml += `<div class="tc-arg">${keyHtml}
        ${renderHighlightedBlock(jsonStr, 'json', 220)}
      </div>`;
    } else {
      // Simple scalar
      argsHtml += `<div class="tc-arg">${keyHtml}<div class="tc-arg-val">${escHtml(String(val ?? ''))}</div></div>`;
    }
  }

  return `<div class="toolcall-block">
    <div class="toolcall-header">
      <span class="tool-badge">📡 ${escHtml(tc.name)}</span>
      <div class="toolcall-header-actions">
        ${writePreviewBtn}
        <button class="copy-btn" data-copy="${escapeAttr(fullJson)}" onclick="copyBtn(this)">Copy JSON</button>
      </div>
    </div>
    <div class="tc-args">${argsHtml}</div>
  </div>`;
}

function renderStructuredResult(parsed, toolName) {
  const blocks = [];
  blocks.push(renderResultMetaGrid(parsed));

  if (Array.isArray(parsed.results) && parsed.results.length) {
    blocks.push(renderSearchResults(parsed.results));
  }

  if (typeof parsed.text === 'string' && parsed.text.trim()) {
    const cleanedText = cleanExternalContent(parsed.text);
    if (parsed.extractMode === 'markdown' || toolName === 'web_fetch') {
      const preview = truncateMultiline(cleanedText, 1800);
      blocks.push(`<div class="arg-preview">${escHtml(preview)}</div>`);
    } else if (toolName === 'exec' || toolName === 'bash') {
      blocks.push(renderHighlightedBlock(parsed.text, 'bash', 260));
    } else if (!Array.isArray(parsed.results)) {
      blocks.push(`<div class="arg-preview">${escHtml(truncateMultiline(cleanedText, 900))}</div>`);
    }
  }

  if (typeof parsed.aggregated === 'string' && parsed.aggregated.trim()) {
    blocks.push(renderHighlightedBlock(parsed.aggregated, 'bash', 260));
  }

  if (typeof parsed.stdout === 'string' && parsed.stdout.trim()) {
    blocks.push(renderHighlightedBlock(parsed.stdout, 'bash', 260));
  }

  if (!blocks.filter(Boolean).length) return '';
  return `<div class="result-rich">${blocks.filter(Boolean).join('')}</div>`;
}

function makeResultSummary(toolName, parsed, raw) {
  const tn = toolName || 'tool';
  if (parsed && typeof parsed === 'object') {
    if (parsed.isError) return `Tool output ${tn}: ${truncateText(parsed.error || parsed.message || 'error', 220)}`;
    if (parsed.status !== undefined) return `Tool output ${tn}: status ${parsed.status}`;
    if (parsed.exitCode !== undefined) return `Tool output ${tn}: exit ${parsed.exitCode}`;
    if (typeof parsed.aggregated === 'string' && parsed.aggregated.trim()) {
      return `Tool output ${tn}: ${truncateText(parsed.aggregated, 220)}`;
    }
    if (typeof parsed.text === 'string' && parsed.text.trim()) {
      return `Tool output ${tn}: ${truncateText(cleanExternalContent(parsed.text), 220)}`;
    }
  }
  return `Tool output ${tn}: ${truncateText(cleanExternalContent(raw), 220)}`;
}

function renderResultBlock(turn, tcOpt) {
  const toolName = turn.tool_name || '';
  const raw = turn.parts.map(p => p.text || '').join('');
  let displayText = raw;
  let lang = 'text';
  let richHtml = '';
  let parsed = null;
  try {
    parsed = JSON.parse(raw);
    displayText = JSON.stringify(parsed, null, 2);
    lang = 'json';
    richHtml = renderStructuredResult(parsed, toolName);
  } catch(e) { /* keep as-is */ }

  const fpPayload = buildFilePreviewFromResult(turn, tcOpt || {}, raw, parsed);
  let summaryFpBtn = '';
  if (fpPayload) {
    const fid = registerFilePreview(fpPayload);
    summaryFpBtn = `<button type="button" class="file-preview-btn file-preview-btn-sm" onclick="event.stopPropagation(); openFilePreviewById('${fid}')">弹窗预览</button>`;
  }

  const preview = truncateText(cleanExternalContent(raw), 160);
  const summary = makeResultSummary(toolName, parsed, raw);
  return `<details class="result-block">
    <summary>
      <span class="arrow">▶</span>
      <span class="result-tool-name">${escHtml(toolName)}</span>
      <span class="result-preview">${escHtml(preview)}</span>
      ${summaryFpBtn}
    </summary>
    <div class="result-inline">
      <div class="result-inline-title">⚡ ${escHtml(toolName || 'tool')} output</div>
      <div class="result-inline-text">${escHtml(summary)}</div>
    </div>
    <div class="result-body">
      ${richHtml}
      <details class="raw-json-wrap" open>
        <summary>查看原始结果</summary>
        ${renderHighlightedBlock(displayText, lang, 320)}
      </details>
    </div>
  </details>`;
}

function escHtml(s) {
  if (typeof s !== 'string') s = String(s || '');
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Boot — run after DOM is ready; setup marked lazily when CDN scripts load
document.addEventListener('DOMContentLoaded', () => {
  setupMarked();
  init().catch(console.error);
});
// Retry setupMarked after deferred scripts finish loading
window.addEventListener('load', () => {
  setupMarked();
  if (currentTranscriptData && currentTaskId) {
    renderTranscript(currentTranscriptData);
  }
});
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default Apache-style logs

    def _parse_cookies(self):
        raw = self.headers.get("Cookie", "")
        c = cookies.SimpleCookie()
        if raw:
            c.load(raw)
        return c

    def _is_authenticated(self) -> bool:
        c = self._parse_cookies()
        morsel = c.get(SESSION_COOKIE)
        token = morsel.value if morsel else None
        return _verify_session_token(token)

    def _render_login(self, error: str | None = None, status: int = 200):
        err_html = f'<div class="error">{error}</div>' if error else ''
        body = LOGIN_HTML.replace('__ERROR__', err_html).encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _require_auth(self) -> bool:
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/login":
            return True
        if self._is_authenticated():
            return True
        if path.startswith("/api/"):
            self.send_json({"error": "unauthorized"}, 401)
        else:
            self._render_login()
        return False

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/login":
            length = int(self.headers.get("Content-Length", "0") or 0)
            raw = self.rfile.read(length).decode("utf-8", errors="replace") if length > 0 else ""
            form = parse_qs(raw)
            username = (form.get("username") or [""])[0]
            password = (form.get("password") or [""])[0]

            if username == AUTH_USERNAME and password == AUTH_PASSWORD:
                token = _make_session_token(username)
                cookie = cookies.SimpleCookie()
                cookie[SESSION_COOKIE] = token
                cookie[SESSION_COOKIE]["path"] = "/"
                cookie[SESSION_COOKIE]["httponly"] = True
                cookie[SESSION_COOKIE]["samesite"] = "Lax"
                cookie[SESSION_COOKIE]["max-age"] = str(SESSION_TTL_SECONDS)
                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", cookie.output(header="").strip())
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.end_headers()
                return

            self._render_login("用户名或密码不正确", status=401)
            return

        if not self._require_auth():
            return

        try:
            if re.match(r"^/api/runs/[\w-]+/tasks/[\w-]+/rerun$", path):
                parts = path.split("/")
                run_id, task_id = parts[-4], parts[-2]
                job = start_task_rerun(run_id, task_id)
                self.send_json(job, 202)
                return
            self.send_json({"error": "method not allowed"}, 405)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_GET(self):
        if not self._require_auth():
            return
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            # ── API routes ──────────────────────────────────────────────────
            if path == "/api/runs":
                self.send_json(get_runs())

            elif path == "/api/leaderboard":
                self.send_json(get_leaderboard())

            elif re.match(r"^/api/runs/[\w-]+$", path):
                run_id = path.split("/")[-1]
                data = get_run_detail(run_id)
                if data is None:
                    self.send_json({"error": "not found"}, 404)
                else:
                    self.send_json(data)

            elif re.match(r"^/api/transcript/[\w-]+/[\w-]+$", path):
                parts = path.split("/")
                run_id, task_id = parts[-2], parts[-1]
                data = get_transcript(run_id, task_id)
                if data is None:
                    self.send_json({"error": "transcript not found"}, 404)
                else:
                    self.send_json(data)

            elif re.match(r"^/api/rerun-jobs/[\w-]+$", path):
                job_id = path.split("/")[-1]
                data = get_rerun_job(job_id)
                if data is None:
                    self.send_json({"error": "job not found"}, 404)
                else:
                    self.send_json(data)

            elif re.match(r"^/api/task/[\w-]+$", path):
                task_id = path.split("/")[-1]
                desc = get_task_description(task_id)
                if desc is None:
                    self.send_json({"error": "task not found"}, 404)
                else:
                    self.send_json({"task_id": task_id, "markdown": desc})

            # ── Static assets ───────────────────────────────────────────────
            elif path.startswith("/assets/"):
                ASSETS_DIR = Path(__file__).parent / "assets"
                filename = path.split("/")[-1]
                # Only serve known safe filenames
                asset_path = ASSETS_DIR / filename
                if asset_path.exists() and asset_path.parent == ASSETS_DIR:
                    content_types = {
                        ".js": "application/javascript",
                        ".css": "text/css",
                    }
                    ext = asset_path.suffix
                    ct = content_types.get(ext, "application/octet-stream")
                    body = asset_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", f"{ct}; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "public, max-age=86400")
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_json({"error": "not found"}, 404)

            # ── SPA ─────────────────────────────────────────────────────────
            else:
                self.send_html(HTML)

        except Exception as e:
            self.send_json({"error": str(e)}, 500)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(
        f"PinchBench Viewer  →  http://localhost:{PORT}"
        "  (修改 viewer.py 后须重启进程，否则 API 仍为旧逻辑)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
