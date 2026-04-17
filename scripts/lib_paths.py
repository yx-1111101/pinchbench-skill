from __future__ import annotations

import re
from pathlib import Path

# This file lives in pinchbench-skill/scripts/ — keep structured results next to legacy
# `results/*.json` under the skill repo (not under ~/.openclaw/workspaces).
SKILL_ROOT = Path(__file__).resolve().parent.parent
RESULTS_ROOT = SKILL_ROOT / "results"

# Task fixtures + agent cwd live under the skill repo (same machine-local policy as results/).
AGENT_WORKSPACE_ROOT = SKILL_ROOT / "agent_workspace"


def normalize_scope(scope: str | None) -> str:
    value = (scope or "formal").strip().lower()
    return value if value in {"formal", "temp"} else "formal"


def normalize_result_key(result_key: str | None) -> str:
    value = (result_key or "all").strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-_")
    return value or "all"


def agent_task_workspace(scope: str, model_slug: str, task_id: str) -> Path:
    return AGENT_WORKSPACE_ROOT / normalize_scope(scope) / model_slug / task_id


def agent_model_workspace(scope: str, model_slug: str) -> Path:
    return AGENT_WORKSPACE_ROOT / normalize_scope(scope) / model_slug


def results_model_dir(scope: str, model_slug: str, result_key: str | None = None) -> Path:
    """One canonical result tree per model/result-key per scope."""
    root = RESULTS_ROOT / normalize_scope(scope) / model_slug
    if result_key is None:
        return root
    return root / normalize_result_key(result_key)


def results_summary_path(scope: str, model_slug: str, result_key: str | None = None) -> Path:
    return results_model_dir(scope, model_slug, result_key) / "summary.json"


def results_transcripts_dir(scope: str, model_slug: str, result_key: str | None = None) -> Path:
    return results_model_dir(scope, model_slug, result_key) / "transcripts"


def iter_summary_paths(scope: str | None = None) -> list[Path]:
    scopes = [normalize_scope(scope)] if scope else ["formal", "temp"]
    paths: list[Path] = []
    for scope_name in scopes:
        root = RESULTS_ROOT / scope_name
        if not root.exists():
            continue
        paths.extend(sorted(root.rglob("summary.json")))
    return paths
