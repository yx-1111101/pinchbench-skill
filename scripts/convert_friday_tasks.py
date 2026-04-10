#!/usr/bin/env python3
"""
Convert OpenFriday task markdown files to PinchBench YAML-frontmatter format.

Reads every task_*.md under FRIDAY_TASKS_ROOT, writes converted files into
PINCHBENCH_TASKS_ROOT/{scene}/task_*.md preserving the scene directory layout.

Run:
    python scripts/convert_friday_tasks.py \
        --friday-root /path/to/openfriday-bench \
        --pinchbench-root /path/to/pinchbench/skill
"""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path


# ── helpers ──────────────────────────────────────────────────────────────

def _extract_timeout(text: str) -> int:
    m = re.search(r"\*\*超时\*\*[：:]\s*(\d+)秒", text)
    return int(m.group(1)) if m else 120


def _extract_grading_type(text: str) -> tuple[str, dict[str, float] | None]:
    """Return (grading_type, grading_weights | None)."""
    if "LLM Judge" in text and "混合" in text:
        # Try to extract explicit weights like "自动 40% + LLM Judge 60%"
        m = re.search(
            r"混合[^)]*?自动\s*(\d+)\s*%\s*\+?\s*LLM\s*Judge\s*(\d+)\s*%",
            text, re.IGNORECASE,
        )
        if not m:
            m = re.search(
                r"自动\s*(\d+)\s*%\s*[+＋]\s*LLM\s*Judge\s*(\d+)\s*%",
                text, re.IGNORECASE,
            )
        if m:
            auto_w = int(m.group(1)) / 100
            llm_w = int(m.group(2)) / 100
            return "hybrid", {"automated": auto_w, "llm_judge": llm_w}
        return "hybrid", {"automated": 0.5, "llm_judge": 0.5}
    if "LLM Judge" in text:
        return "llm_judge", None
    return "automated", None


def _extract_task_id(text: str, filename_stem: str) -> str:
    m = re.search(r"^#\s+(task_\S+)", text, re.MULTILINE)
    return m.group(1).strip() if m else filename_stem


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a ## heading until the next ## or end."""
    pattern = rf"##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _extract_grade_python(text: str) -> str:
    """Extract the python code block that contains `def grade(`."""
    for block in re.finditer(r"```python\s*\n(.*?)```", text, re.DOTALL):
        if "def grade(" in block.group(1):
            return block.group(1).strip()
    return ""


def _extract_name_from_header(text: str) -> str:
    """Derive a human-readable name from the first **能力** line or task id."""
    m = re.search(r"\*\*能力\*\*[：:]\s*(.+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+task_\S+", text, re.MULTILINE)
    if m:
        return m.group(0).lstrip("# ").strip()
    return "Unknown"


def _adapt_grade_signature(code: str) -> str:
    """Convert grade(workspace_path, transcript) -> grade(transcript, workspace_path).

    Also injects `from pathlib import Path; workspace_path = Path(workspace_path)`
    at the top of the function body so the rest of the code (which expects a Path)
    keeps working.
    """
    # Replace the signature
    code = re.sub(
        r"def\s+grade\s*\(\s*workspace_path\s*,\s*transcript\s*\)",
        "def grade(transcript, workspace_path)",
        code,
    )

    # Inject Path conversion right after the signature line
    lines = code.split("\n")
    result = []
    injected = False
    for line in lines:
        result.append(line)
        if not injected and line.strip().startswith("def grade("):
            indent = "    "
            result.append(f"{indent}from pathlib import Path")
            result.append(f"{indent}workspace_path = Path(workspace_path)")
            injected = True
    return "\n".join(result)


def _build_criteria_checklist(criteria_text: str) -> str:
    """Convert OpenFriday 评分标准 items into PinchBench checklist."""
    lines = []
    for line in criteria_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Already checklist
        if re.match(r"^-\s+\[[ x]\]", line):
            lines.append(line)
            continue
        # Bullet with backtick key
        m = re.match(r"^[-\*]\s+`(\w+)`[：:]\s*(.*)", line)
        if m:
            lines.append(f"- [ ] {m.group(1)}: {m.group(2)}")
            continue
        # Bare bullet
        m = re.match(r"^[-\*]\s+(.*)", line)
        if m:
            lines.append(f"- [ ] {m.group(1)}")
            continue
        # Sub-headers like **自动**：
        if line.startswith("**") and "：" in line:
            continue
        # Skip LLM Judge description lines
        if "LLM Judge" in line:
            continue
        if line:
            lines.append(f"- [ ] {line}")
    return "\n".join(lines)


def _build_llm_rubric(criteria_text: str, task_desc: str) -> str:
    """Build an LLM Judge Rubric section from the task description."""
    dims_parts: list[str] = []
    found_judge = False
    for line in criteria_text.split("\n"):
        if "LLM Judge" in line:
            found_judge = True
            # Extract inline text after ：(if any)
            m = re.search(r"LLM\s*Judge\*{0,2}[：:]\s*(.*)", line)
            if m and m.group(1).strip():
                dims_parts.append(m.group(1).strip())
            continue
        if found_judge:
            stripped = line.strip()
            if stripped.startswith("- "):
                dims_parts.append(stripped[2:])
            elif stripped and not stripped.startswith("**"):
                dims_parts.append(stripped)
            else:
                break
    dims = " · ".join(dims_parts) if dims_parts else "评价输出的准确性、结构清晰度和实用性"

    return textwrap.dedent(f"""\
        ### Quality Assessment

        Evaluate the agent's output against the task requirements.

        Dimensions: {dims}

        **Score 1.0**: Fully meets all requirements with high quality
        **Score 0.75**: Meets most requirements with minor gaps
        **Score 0.5**: Partially meets requirements
        **Score 0.25**: Significant gaps or quality issues
        **Score 0.0**: Does not address the task""")


# ── main conversion ─────────────────────────────────────────────────────

def convert_task(
    src_path: Path,
    scene: str,
    friday_root: Path,
    pinchbench_root: Path,
) -> Path:
    text = src_path.read_text(encoding="utf-8")
    task_id = _extract_task_id(text, src_path.stem)
    name = _extract_name_from_header(text)
    timeout = _extract_timeout(text)
    grading_type, grading_weights = _extract_grading_type(text)

    task_desc = _extract_section(text, "任务说明")
    criteria_text = _extract_section(text, "评分标准")
    grade_code = _extract_grade_python(text)

    # Check if dataset dir exists
    dataset_dir_rel = f"dataset/{scene}/{task_id}"
    dataset_exists = (friday_root / "dataset" / scene / task_id).is_dir()

    # Build YAML frontmatter
    fm_lines = [
        "---",
        f"id: {task_id}",
        f"name: \"{name}\"",
        f"category: {scene}",
        f"grading_type: {grading_type}",
        f"timeout_seconds: {timeout}",
        "workspace_files: []",
    ]
    if dataset_exists:
        fm_lines.append(f"dataset_dir: {dataset_dir_rel}")
    if grading_weights:
        fm_lines.append("grading_weights:")
        for k, v in grading_weights.items():
            fm_lines.append(f"  {k}: {v}")
    fm_lines.append("---")

    # Build body sections
    body_parts = []

    # Prompt
    body_parts.append(f"## Prompt\n\n{task_desc}")

    # Expected Behavior (derive from criteria description)
    expected = f"The agent should complete the task as described in the prompt."
    if criteria_text:
        expected += f"\n\nEvaluation criteria:\n{criteria_text}"
    body_parts.append(f"## Expected Behavior\n\n{expected}")

    # Grading Criteria
    checklist = _build_criteria_checklist(criteria_text)
    if checklist:
        body_parts.append(f"## Grading Criteria\n\n{checklist}")

    # Automated Checks
    if grade_code:
        adapted = _adapt_grade_signature(grade_code)
        body_parts.append(f"## Automated Checks\n\n```python\n{adapted}\n```")

    # LLM Judge Rubric (for hybrid and llm_judge tasks)
    if grading_type in ("hybrid", "llm_judge"):
        rubric = _build_llm_rubric(criteria_text, task_desc)
        body_parts.append(f"## LLM Judge Rubric\n\n{rubric}")

    output = "\n".join(fm_lines) + "\n\n" + "\n\n".join(body_parts) + "\n"

    dest_dir = pinchbench_root / "tasks" / scene
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{task_id}.md"
    dest_path.write_text(output, encoding="utf-8")
    return dest_path


def main():
    parser = argparse.ArgumentParser(description="Convert OpenFriday tasks to PinchBench format")
    parser.add_argument(
        "--friday-root",
        required=True,
        help="Path to openfriday-bench repo root",
    )
    parser.add_argument(
        "--pinchbench-root",
        required=True,
        help="Path to pinchbench/skill repo root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files",
    )
    args = parser.parse_args()

    friday_root = Path(args.friday_root).resolve()
    pinchbench_root = Path(args.pinchbench_root).resolve()
    friday_tasks = friday_root / "tasks"

    if not friday_tasks.is_dir():
        print(f"Error: {friday_tasks} not found")
        return

    scenes = [d.name for d in friday_tasks.iterdir() if d.is_dir() and not d.name.startswith(".")]
    converted = 0
    errors = 0

    for scene in sorted(scenes):
        scene_dir = friday_tasks / scene
        task_files = sorted(scene_dir.glob("task_*.md"))
        print(f"\n[{scene}] {len(task_files)} tasks")

        for tf in task_files:
            try:
                if args.dry_run:
                    print(f"  would convert: {tf.name}")
                else:
                    dest = convert_task(tf, scene, friday_root, pinchbench_root)
                    print(f"  converted: {tf.name} -> {dest.relative_to(pinchbench_root)}")
                converted += 1
            except Exception as e:
                print(f"  ERROR converting {tf.name}: {e}")
                errors += 1

    print(f"\nDone: {converted} converted, {errors} errors")


if __name__ == "__main__":
    main()
