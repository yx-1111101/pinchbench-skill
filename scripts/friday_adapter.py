"""
Friday Adapter — extends PinchBench to support OpenFriday-style tasks.

This module provides subclasses and wrapper functions that integrate OpenFriday
tasks into PinchBench without modifying PinchBench's original source code.

Usage:
    from friday_adapter import FridayTaskLoader, prepare_friday_workspace
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib_tasks import Task, TaskLoader
from lib_agent import (
    _get_agent_workspace,
    _get_agent_store_dir,
    prepare_task_workspace,
)

logger = logging.getLogger(__name__)


class FridayTaskLoader(TaskLoader):
    """TaskLoader that supports subdirectory scanning for OpenFriday scene layout.

    PinchBench's original TaskLoader uses a flat ``glob("task_*.md")``.
    This subclass uses ``rglob`` so tasks organised as
    ``tasks/{scene}/task_*.md`` are discovered alongside flat tasks.
    """

    def load_all_tasks(self, category_filter: Optional[str] = None) -> List[Task]:
        tasks = []
        task_files = sorted(self.tasks_dir.rglob("task_*.md"))
        logger.info("FridayTaskLoader found %d task files (rglob)", len(task_files))

        for task_file in task_files:
            try:
                task = self.load_task(task_file)
                if "_XX_" in task.task_id or task.task_id == "task_XX_name":
                    continue
                if category_filter and task.category != category_filter:
                    continue
                tasks.append(task)
                logger.info("Loaded task: %s", task.task_id)
            except Exception as e:
                logger.error("Failed to load %s: %s", task_file, e, exc_info=True)

        logger.info("FridayTaskLoader: %d tasks loaded", len(tasks))
        return tasks


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
