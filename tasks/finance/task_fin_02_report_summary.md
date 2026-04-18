---
id: task_fin_02_report_summary
name: "PDF研报解析与核心数据摘要"
category: finance
grading_type: hybrid
timeout_seconds: 540
workspace_files:
  - industry_report.pdf
dataset_dir: dataset/finance/task_fin_02_report_summary
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

工作区有一份行业研报 `industry_report.pdf`，请阅读后生成摘要文件 `report_summary.md`，包含：

- 核心观点（3-5 条）
- 关键数据指标（市场规模、增速、份额等）
- 主要风险提示
- 投资建议（如有）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：report_summary.md 存在
- `file_not_empty`：内容非空
- `has_key_points`：包含「核心」「观点」「要点」或数字列表
- `has_data`：包含数字和单位（%、亿、万、billion）
- `has_risk_section`：包含「风险」「risk」相关词

**LLM Judge**：摘要准确性 · 数据提取完整性 · 结构清晰度

## Grading Criteria

- [ ] file_created: report_summary.md 存在
- [ ] file_not_empty: 内容非空
- [ ] has_key_points: 包含「核心」「观点」「要点」或数字列表
- [ ] has_data: 包含数字和单位（%、亿、万、billion）
- [ ] has_risk_section: 包含「风险」「risk」相关词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "report_summary.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_key_points","has_data","has_risk_section"]}
    content = f.read_text(encoding="utf-8").strip()
    has_points = any(w in content for w in ["核心","观点","要点","结论"]) or bool(re.search(r'^\d+[\.\、]', content, re.M))
    has_data = bool(re.search(r'\d+[\.,]?\d*\s*[%％亿万billion trillion]', content))
    has_risk = any(w in content.lower() for w in ["风险","risk","注意","警示","不确定"])
    return {
        "file_created":    1.0,
        "file_not_empty":  1.0 if len(content) > 0 else 0.0,
        "has_key_points":  1.0 if has_points else 0.0,
        "has_data":        1.0 if has_data else 0.0,
        "has_risk_section":1.0 if has_risk else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 摘要准确性 · 数据提取完整性 · 结构清晰度摘要准确性 · 数据提取完整性 · 结构清晰度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
