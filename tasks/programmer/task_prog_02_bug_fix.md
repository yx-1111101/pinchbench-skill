---
id: task_prog_02_bug_fix
name: "报错日志定位 → 运行时 Bug 修复"
category: programmer
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - clean_sales.py
  - error.log
dataset_dir: dataset/programmer/task_prog_02_bug_fix
grading_weights:
  automated: 0.7
  llm_judge: 0.3
---

## Prompt

工作区有一个 pandas 数据清洗脚本 `clean_sales.py` 和一份运行崩溃日志 `error.log`。

这个脚本在每日凌晨跑批时崩溃了，请你：

1. 阅读 `error.log`，定位全部 Bug
2. 修复 `clean_sales.py` 中的所有问题
3. 将 Bug 分析和修复说明写入 `bug_report.md`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：bug_report.md 存在
- `script_runs`：修复后的 clean_sales.py 能无异常运行（`python clean_sales.py --test` 返回码为 0）
- `output_correct`：输出符合 golden answer（`valid_rows: 6, revenue: 2150.5, top_region: 华东`）
- `all_bugs_mentioned`：bug_report.md 中涵盖了全部3处 Bug 的关键词

**LLM Judge**：根因描述是否准确 · 修复方案是否最优 · 报告是否清晰

## Grading Criteria

- [ ] file_created: bug_report.md 存在
- [ ] script_runs: 修复后的 clean_sales.py 能无异常运行（`python clean_sales.py --test` 返回码为 0）
- [ ] output_correct: 输出符合 golden answer（`valid_rows: 6, revenue: 2150.5, top_region: 华东`）
- [ ] all_bugs_mentioned: bug_report.md 中涵盖了全部3处 Bug 的关键词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import subprocess, re
    report = workspace_path / "bug_report.md"
    script = workspace_path / "clean_sales.py"

    if not report.exists():
        return {k: 0.0 for k in ["file_created","script_runs","output_correct","all_bugs_mentioned"]}

    report_text = report.read_text(encoding="utf-8")

    script_runs = output_correct = False
    if script.exists():
        try:
            r = subprocess.run(
                ["python", str(script), "--test"],
                capture_output=True, text=True, timeout=30, cwd=str(workspace_path)
            )
            script_runs = (r.returncode == 0)
            out = r.stdout
            output_correct = (
                "valid_rows: 6" in out and
                "revenue: 2150.5" in out and
                "top_region: 华东" in out
            )
        except Exception:
            pass

    bug_kw_groups = [
        ["astype", "TypeError", "类型转换", "int", "float", "强转", "类型错误"],   # bug1
        ["NaN", "fillna", "dropna", "空值", "缺失值", "isnull", "isna"],           # bug2
        ["SettingWithCopy", "chained", "loc", "copy", "链式赋值", "写回"],         # bug3
    ]
    bugs_found = sum(1 for grp in bug_kw_groups if any(kw in report_text for kw in grp))

    return {
        "file_created":      1.0,
        "script_runs":       1.0 if script_runs else 0.0,
        "output_correct":    1.0 if output_correct else 0.0,
        "all_bugs_mentioned":1.0 if bugs_found >= 3 else (0.5 if bugs_found == 2 else 0.0),
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 根因描述是否准确 · 修复方案是否最优 · 报告是否清晰根因描述是否准确 · 修复方案是否最优 · 报告是否清晰

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
