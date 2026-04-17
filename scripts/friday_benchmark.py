#!/usr/bin/env python3
"""
Friday Benchmark — runs OpenFriday tasks through PinchBench infrastructure.

This is a thin entry-point that:
  1. Uses FridayTaskLoader (rglob for subdirectory scanning)
  2. Monkey-patches prepare_task_workspace to support dataset_dir
  3. Delegates all execution, grading, logging, and upload to PinchBench

Usage:
  uv run scripts/friday_benchmark.py --model anthropic/claude-sonnet-4
  uv run scripts/friday_benchmark.py --model anthropic/claude-sonnet-4 --category foundation
"""

from __future__ import annotations

import lib_agent
from friday_adapter import FridayTaskLoader, prepare_friday_workspace

# Monkey-patch so execute_openclaw_task picks up dataset_dir handling
lib_agent.prepare_task_workspace = prepare_friday_workspace

# Now import benchmark's main — it uses the patched module
from benchmark import (
    BenchmarkRunner,
    _parse_args,
    main as _pinchbench_main,
)


class FridayBenchmarkRunner(BenchmarkRunner):
    """BenchmarkRunner that uses FridayTaskLoader for subdirectory scanning."""

    def __init__(self, tasks_dir):
        super().__init__(tasks_dir)
        self.task_loader = FridayTaskLoader(tasks_dir)

    def load_tasks(self) -> None:
        import logging
        logger = logging.getLogger("benchmark")
        logger.info("Loading tasks (Friday mode: rglob + category filter)...")
        self.tasks = self.task_loader.load_all_tasks(
            category_filter=getattr(self, "_category_filter", None)
        )
        logger.info(f"Loaded {len(self.tasks)} tasks")


def main():
    import argparse
    import json
    import logging
    import os
    import statistics
    import sys
    import time
    from pathlib import Path

    from lib_agent import (
        cleanup_agent_sessions,
        ensure_agent_exists,
        execute_openclaw_task,
        ModelValidationError,
        slugify_model,
        validate_openrouter_model,
    )
    from lib_grading import GradeResult, grade_task

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("benchmark.log")],
    )
    logger = logging.getLogger("benchmark")

    script_dir = Path(__file__).parent
    skill_root = script_dir.parent
    tasks_dir = skill_root / "tasks"

    logger.info("🦀 Friday Benchmark — OpenFriday tasks via PinchBench")

    if not tasks_dir.exists():
        logger.error("Tasks directory not found: %s", tasks_dir)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Friday Benchmark — OpenFriday tasks via PinchBench",
    )
    parser.add_argument("--model", required=False, help="Model identifier")
    parser.add_argument("--suite", default="all", help="Task suite filter")
    parser.add_argument("--category", default=None, help="Only run tasks in this category (e.g. foundation, secretary)")
    parser.add_argument("--output-dir", default="results", help="Results directory")
    parser.add_argument("--register", action="store_true", help="Register API token")
    parser.add_argument("--no-upload", action="store_true", help="Skip upload")
    parser.add_argument("--upload", type=str, metavar="RESULTS_JSON", help="Upload previous results")
    parser.add_argument("--timeout-multiplier", type=float, default=1.0, help="Scale timeouts")
    parser.add_argument("--runs", type=int, default=1, help="Runs per task")
    parser.add_argument(
        "--judge",
        default=None,
        help="Judge model for LLM grading (default: openrouter/anthropic/claude-opus-4.5)",
    )
    parser.add_argument(
        "--judge-backend",
        choices=("api", "openclaw"),
        default="api",
        help="LLM judge backend (default: api)",
    )
    parser.add_argument("--base-url", default=None, help="Custom API base URL")
    parser.add_argument("--api-key", default=None, help="API key for custom endpoint")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--official-key", type=str, metavar="KEY", help="Official submission key")
    parser.add_argument("--no-fail-fast", action="store_true", help="Continue on sanity failure")
    parser.add_argument("--trend", action="store_true", help="Run trend analysis")
    parser.add_argument("--trend-window", type=int, default=10, help="Trend window size")
    parser.add_argument("--trend-threshold", type=float, default=-0.5, help="Trend regression threshold")
    args = parser.parse_args()

    if not args.model and not args.register and not args.upload:
        logger.error("Missing required argument: --model")
        sys.exit(2)

    # Handle --register / --upload by delegating to PinchBench
    if args.register or args.upload:
        _pinchbench_main()
        return

    runner = FridayBenchmarkRunner(tasks_dir)
    runner._category_filter = args.category
    runner.load_tasks()

    if not runner.tasks:
        logger.error("No tasks found (category=%s)", args.category)
        sys.exit(1)

    model_slug = slugify_model(args.model)

    # Determine run_id
    run_root = Path("/tmp/pinchbench")
    run_root.mkdir(parents=True, exist_ok=True)
    existing = []
    for entry in run_root.iterdir():
        if entry.is_dir():
            try:
                existing.append(int(entry.name))
            except ValueError:
                pass
    run_id = str(max(existing) + 1 if existing else 1)

    agent_id = f"bench-{model_slug}"
    agent_workspace = Path(f"/tmp/pinchbench/{run_id}/agent_workspace")

    if args.base_url:
        logger.info("Using custom endpoint: %s", args.base_url)
    else:
        try:
            validate_openrouter_model(args.model)
        except ModelValidationError as exc:
            logger.error("Model validation failed: %s", exc)
            sys.exit(1)

    ensure_agent_exists(
        agent_id, args.model, agent_workspace,
        base_url=args.base_url, api_key=args.api_key,
    )
    cleanup_agent_sessions(agent_id)

    # Build task list respecting --suite
    task_ids = None
    if args.suite != "all":
        if args.suite == "automated-only":
            task_ids = [t.task_id for t in runner.tasks if t.grading_type == "automated"]
        else:
            task_ids = [tid.strip() for tid in args.suite.split(",") if tid.strip()]

    tasks_to_run = runner.tasks
    if task_ids is not None:
        tasks_to_run = [t for t in runner.tasks if t.task_id in task_ids]
    tasks_by_id = {t.task_id: t for t in tasks_to_run}

    runs_per_task = max(1, args.runs)
    results = []
    grades_by_task_id = {}

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    incremental_path = output_dir / f"{run_id}_{model_slug}.json"

    def _write_incremental():
        entries = [
            {
                "task_id": r["task_id"],
                "status": r["status"],
                "timed_out": r["timed_out"],
                "execution_time": r["execution_time"],
                "transcript_length": len(r["transcript"]),
                "usage": r.get("usage", {}),
                "workspace": r["workspace"],
                "grading": grades_by_task_id.get(r["task_id"], {}),
                "frontmatter": tasks_by_id[r["task_id"]].frontmatter,
            }
            for r in results
        ]
        partial = {
            "model": args.model,
            "run_id": run_id,
            "timestamp": time.time(),
            "suite": args.suite,
            "category": args.category,
            "runs_per_task": runs_per_task,
            "tasks": entries,
            "in_progress": True,
            "completed_tasks": len(grades_by_task_id),
            "total_tasks": len(tasks_to_run),
        }
        try:
            incremental_path.write_text(json.dumps(partial, indent=2), encoding="utf-8")
        except OSError:
            pass

    for i, task in enumerate(tasks_to_run, 1):
        task_grades = []
        task_results = []
        for run_idx in range(runs_per_task):
            logger.info("\n%s", "=" * 80)
            logger.info(
                "Task %s/%s (Run %s/%s): %s [%s]",
                i, len(tasks_to_run), run_idx + 1, runs_per_task,
                task.task_id, task.category,
            )
            logger.info("%s", "=" * 80)
            execution_error = None
            try:
                result = execute_openclaw_task(
                    task=task,
                    agent_id=agent_id,
                    model_id=args.model,
                    run_id=f"{run_id}-{run_idx + 1}",
                    timeout_multiplier=args.timeout_multiplier,
                    skill_dir=skill_root,
                    output_dir=output_dir / f"{run_id}_transcripts",
                    verbose=args.verbose,
                )
            except Exception as exc:
                execution_error = str(exc)
                logger.warning("Execution failed for %s: %s", task.task_id, exc)
                result = {
                    "agent_id": agent_id,
                    "task_id": task.task_id,
                    "status": "error",
                    "transcript": [],
                    "usage": {},
                    "workspace": "",
                    "exit_code": -1,
                    "timed_out": False,
                    "execution_time": 0.0,
                    "stdout": "",
                    "stderr": execution_error,
                }

            try:
                grade_kwargs = dict(
                    task=task, execution_result=result, skill_dir=skill_root,
                    judge_backend=args.judge_backend,
                    verbose=args.verbose,
                )
                if args.judge:
                    grade_kwargs["judge_model"] = args.judge
                grade = grade_task(**grade_kwargs)
            except Exception as exc:
                note = f"Grading failed: {exc}"
                if execution_error:
                    note = f"Execution: {execution_error}; {note}"
                logger.warning("Grading failed for %s: %s", task.task_id, exc)
                grade = GradeResult(
                    task_id=task.task_id, score=0.0, max_score=1.0,
                    grading_type=task.grading_type, breakdown={}, notes=note,
                )

            task_grades.append(grade)
            task_results.append(result)
            results.append(result)

            score_pct = grade.score / grade.max_score * 100 if grade.max_score > 0 else 0
            icon = "OK" if grade.score >= grade.max_score else "PARTIAL" if grade.score > 0 else "FAIL"
            logger.info(
                "[%s] %s: %.1f/%.1f (%.0f%%) - %s",
                icon, task.task_id, grade.score, grade.max_score, score_pct, grade.grading_type,
            )
            if grade.notes:
                logger.info("   Notes: %s", grade.notes[:200])

        task_scores = [g.score for g in task_grades]
        grades_by_task_id[task.task_id] = {
            "runs": [g.to_dict() for g in task_grades],
            "mean": statistics.mean(task_scores),
            "std": statistics.stdev(task_scores) if len(task_scores) > 1 else 0.0,
            "min": min(task_scores),
            "max": max(task_scores),
        }
        _write_incremental()

    # Final results
    task_entries = [
        {
            "task_id": r["task_id"],
            "status": r["status"],
            "timed_out": r["timed_out"],
            "execution_time": r["execution_time"],
            "transcript_length": len(r["transcript"]),
            "usage": r.get("usage", {}),
            "workspace": r["workspace"],
            "grading": grades_by_task_id[r["task_id"]],
            "frontmatter": tasks_by_id[r["task_id"]].frontmatter,
        }
        for r in results
    ]
    aggregate = {
        "model": args.model,
        "run_id": run_id,
        "timestamp": time.time(),
        "suite": args.suite,
        "category": args.category,
        "runs_per_task": runs_per_task,
        "tasks": task_entries,
    }
    final_path = output_dir / f"{run_id}_{model_slug}.json"
    final_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
    logger.info("Results saved to %s", final_path)

    # Score summary by category
    cat_scores: dict[str, list[float]] = {}
    for tid, gdata in grades_by_task_id.items():
        cat = tasks_by_id[tid].category if tid in tasks_by_id else "unknown"
        cat_scores.setdefault(cat, []).append(gdata["mean"])

    logger.info("\n%s", "=" * 60)
    logger.info("FRIDAY BENCHMARK SCORE SUMMARY")
    logger.info("%s", "=" * 60)
    total_earned = sum(g["mean"] for g in grades_by_task_id.values())
    total_possible = float(len(grades_by_task_id))
    overall_pct = (total_earned / total_possible * 100) if total_possible > 0 else 0
    logger.info("   Overall: %.1f%% (%.1f / %.0f)", overall_pct, total_earned, total_possible)
    logger.info("")
    logger.info("   %-20s %8s %8s", "CATEGORY", "SCORE", "TASKS")
    logger.info("   %s", "-" * 40)
    for cat in sorted(cat_scores.keys()):
        scores = cat_scores[cat]
        earned = sum(scores)
        pct = earned / len(scores) * 100 if scores else 0
        logger.info("   %-20s %6.1f%% %6d", cat.upper(), pct, len(scores))
    logger.info("   %s", "-" * 40)

    # Upload unless --no-upload
    if not args.no_upload:
        try:
            from lib_upload import UploadError, upload_results
            result = upload_results(final_path, official_key=args.official_key)
            if result.rank is not None:
                logger.info("Uploaded: rank #%s", result.rank)
            if result.leaderboard_url:
                logger.info("View at: %s", result.leaderboard_url)
        except Exception as exc:
            logger.warning("Upload skipped: %s", exc)
    else:
        logger.info("Skipping upload (--no-upload)")


if __name__ == "__main__":
    main()
