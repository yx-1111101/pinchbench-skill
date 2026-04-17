"""
Friday Adapter — thin OpenFriday-specific hooks for PinchBench.

The shared benchmark flow now lives in ``benchmark.py`` and ``lib_tasks.py``.
This module only keeps the two Friday-specific behaviors:
1. Recursively discover tasks under ``tasks/<scene>/task_*.md``
2. Overlay ``dataset_dir`` contents into the prepared workspace

Usage:
    from friday_adapter import FridayTaskLoader, prepare_friday_workspace
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from lib_tasks import Task, TaskLoader
from lib_agent import prepare_task_workspace

logger = logging.getLogger(__name__)


class FridayTaskLoader(TaskLoader):
    """TaskLoader that recursively discovers Friday tasks.

    PinchBench's base loader uses a flat ``glob("task_*.md")``.
    OpenFriday tasks live one level deeper at ``tasks/<scene>/task_*.md``,
    so this subclass swaps in ``rglob``. Template/category filtering is
    handled by the base class.
    """

    def _discover_task_files(self) -> List[Path]:
        return sorted(self.tasks_dir.rglob("task_*.md"))


def prepare_friday_workspace(
    skill_dir: Path,
    run_id: str,
    task: Task,
    agent_id: str,
) -> Path:
    """Prepare workspace using PinchBench's original logic, then overlay dataset_dir.

    This wraps ``prepare_task_workspace`` and adds bulk-copy of
    ``dataset_dir`` from the task frontmatter — the pattern used by
    OpenFriday tasks.
    """
    workspace = prepare_task_workspace(skill_dir, run_id, task, agent_id)

    dataset_rel = task.frontmatter.get("dataset_dir", "")
    if dataset_rel:
        dataset_path = skill_dir / dataset_rel
        if dataset_path.is_dir():
            for src_file in dataset_path.rglob("*"):
                if src_file.is_file():
                    rel = src_file.relative_to(dataset_path)
                    dest = workspace / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(src_file.read_bytes())
            logger.info("Copied dataset dir %s to workspace", dataset_rel)
        else:
            logger.warning("dataset_dir specified but not found: %s", dataset_path)

    return workspace
