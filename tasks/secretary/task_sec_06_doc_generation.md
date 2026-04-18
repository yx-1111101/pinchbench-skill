---
id: task_sec_06_doc_generation
name: "结构化文档生成（周报 / 纪要）"
category: secretary
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - work_log.txt
dataset_dir: dataset/secretary/task_sec_06_doc_generation
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有一份零散的本周工作记录 `work_log.txt`，请生成一份规范的**周报** `weekly_report.md`，包含：

- 标题 + 周次 + 日期范围
- 本周完成事项（分条列出）
- 下周计划（分条列出）
- 需要协调/上升的问题（如有）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created` · `has_title` · `has_completed_section` · `has_next_week_section` · `item_count_sufficient`（完成事项≥4条）

**LLM Judge**：内容提炼质量 · 语言专业规范 · 结构完整清晰

## Grading Criteria

- [ ] `file_created` · `has_title` · `has_completed_section` · `has_next_week_section` · `item_count_sufficient`（完成事项≥4条）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "weekly_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_title","has_completed_section","has_next_week_section","item_count_sufficient"]}
    content = f.read_text(encoding="utf-8")
    has_title = content.strip().startswith("#")
    has_completed = any(w in content for w in ["本周","完成","已完成","这周"])
    has_next_week = any(w in content for w in ["下周","下周计划","next week","待办"])
    # 计算列表项数量（- 或数字开头的行）
    items = re.findall(r'^[\-\*\d]', content, re.MULTILINE)
    item_count_ok = len(items) >= 4
    return {
        "file_created":          1.0,
        "has_title":             1.0 if has_title else 0.0,
        "has_completed_section": 1.0 if has_completed else 0.0,
        "has_next_week_section": 1.0 if has_next_week else 0.0,
        "item_count_sufficient": 1.0 if item_count_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 内容提炼质量 · 语言专业规范 · 结构完整清晰内容提炼质量 · 语言专业规范 · 结构完整清晰

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
