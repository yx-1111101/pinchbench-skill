---
id: task_twin_03_value_map
name: "冷启动 — 历史决策记录 → 总结判断逻辑与边界"
category: digital_twin
grading_type: hybrid
timeout_seconds: 150
workspace_files: []
dataset_dir: dataset/digital_twin/task_twin_03_value_map
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

工作区有陈默过去12个月的决策日志 `decision_log.txt`，记录了他在工作中做过的20个决策及理由。

请分析后生成决策逻辑报告 `value_map.md`，包含：

1. **核心价值观**：从决策中归纳出3-5条他最看重的原则
2. **典型拒绝模式**：他通常在什么情况下说「不」
3. **典型接受模式**：他通常在什么情况下说「是」
4. **判断盲点或偏好**：有没有明显的非理性偏好
5. **硬边界清单**：绝对不会做的事

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：value_map.md 存在
- `file_not_empty`：内容超过 400 字
- `has_principles`：包含价值观相关词（原则/价值/看重/优先）
- `has_reject_pattern`：包含拒绝相关词（拒绝/不接受/不会/红线）
- `mentions_key_decisions`：提到 decision_log 中的关键词（媒体/投资/合同/猎头/KOL/供应商）

**LLM Judge**：归纳是否准确 · 原则是否具体 · 边界是否可被后续任务直接引用

## Grading Criteria

- [ ] file_created: value_map.md 存在
- [ ] file_not_empty: 内容超过 400 字
- [ ] has_principles: 包含价值观相关词（原则/价值/看重/优先）
- [ ] has_reject_pattern: 包含拒绝相关词（拒绝/不接受/不会/红线）
- [ ] mentions_key_decisions: 提到 decision_log 中的关键词（媒体/投资/合同/猎头/KOL/供应商）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "value_map.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_principles",
                                   "has_reject_pattern","mentions_key_decisions"]}
    content = f.read_text(encoding="utf-8").strip()
    principle_kws = ["原则","价值","看重","优先","核心","相信"]
    reject_kws    = ["拒绝","不接受","不会","红线","边界","绝对不"]
    case_kws      = ["媒体","投资","合同","猎头","KOL","供应商","并购","外包"]
    return {
        "file_created":           1.0,
        "file_not_empty":         1.0 if len(content) > 400 else 0.0,
        "has_principles":         1.0 if sum(1 for w in principle_kws if w in content) >= 2 else 0.0,
        "has_reject_pattern":     1.0 if sum(1 for w in reject_kws if w in content) >= 2 else 0.0,
        "mentions_key_decisions": 1.0 if sum(1 for w in case_kws if w in content) >= 3 else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 归纳是否准确 · 原则是否具体 · 边界是否可被后续任务直接引用归纳是否准确 · 原则是否具体 · 边界是否可被后续任务直接引用

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
