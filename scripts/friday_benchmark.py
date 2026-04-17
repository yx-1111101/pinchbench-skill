#!/usr/bin/env python3
"""
Friday benchmark compatibility wrapper.

This entry point keeps only the two Friday-specific behaviors:
1. Recursively discover ``tasks/<scene>/task_*.md`` via ``FridayTaskLoader``.
2. Populate the workspace from a task's ``dataset_dir`` via
   ``prepare_friday_workspace``.

All other logic (argument parsing, execution, grading, result writing,
category summary, upload) is delegated to ``benchmark.py``.

Usage:
    uv run scripts/friday_benchmark.py --model anthropic/claude-sonnet-4
    uv run scripts/friday_benchmark.py --model anthropic/claude-sonnet-4 --category foundation
"""

from __future__ import annotations

import benchmark
import lib_agent
from friday_adapter import FridayTaskLoader, prepare_friday_workspace


class FridayBenchmarkRunner(benchmark.BenchmarkRunner):
    """BenchmarkRunner that plugs in the recursive Friday task loader."""

    def __init__(self, tasks_dir):
        super().__init__(tasks_dir, task_loader=FridayTaskLoader(tasks_dir))


def main() -> None:
    # Friday tasks can declare a `dataset_dir` in their frontmatter; the
    # adapter copies that directory on top of the standard workspace layout.
    lib_agent.prepare_task_workspace = prepare_friday_workspace

    # Swap in the recursive loader so BenchmarkRunner picks up
    # `tasks/<scene>/task_*.md`.
    benchmark.BenchmarkRunner = FridayBenchmarkRunner

    benchmark.main()


if __name__ == "__main__":
    main()
