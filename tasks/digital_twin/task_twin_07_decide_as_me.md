---
id: task_twin_07_decide_as_me
name: "调用执行 — 给商业情境，给出「陈默会怎么判断」"
category: digital_twin
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - value_map.md
  - scenarios.txt
dataset_dir: dataset/digital_twin/task_twin_07_decide_as_me
grading_weights:
  automated: 0.3
  llm_judge: 0.7
---

## Prompt

工作区有陈默的价值观地图 `value_map.md` 和3个商业判断情境 `scenarios.txt`。

请以陈默视角对每个情境给出判断，保存到 `decisions.md`：

- **情境一**：一个 DAU 10万的小工具 App 找陈默投资，估值500万，要求两周内给答复
- **情境二**：猎头要求先付5000元「定向搜索费」才介绍候选人
- **情境三**：媒体邀请做专题报道，不收费，只要分享团队管理方法（边界事项）

格式：`情境X | 判断：接受/拒绝/需更多信息 | 理由：... | 置信度：高/中/低`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：decisions.md 存在
- `has_three_decisions`：包含三个情境的判断
- `boundary_respected`：情境三包含边界提示词
- `has_confidence_levels`：包含置信度标注

**LLM Judge**：判断是否符合 value_map 的逻辑 · 理由是否有陈默式论证 · 边界情境是否正确降级

## Grading Criteria

- [ ] file_created: decisions.md 存在
- [ ] has_three_decisions: 包含三个情境的判断
- [ ] boundary_respected: 情境三包含边界提示词
- [ ] has_confidence_levels: 包含置信度标注

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "decisions.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_three_decisions",
                                   "boundary_respected","has_confidence_levels"]}
    content = f.read_text(encoding="utf-8")
    has_three    = sum(1 for p in ["情境一","情境二","情境三"] if p in content) >= 3
    boundary_kws = ["边界","媒体","不在范围","请确认","超出","建议本人"]
    boundary_ok  = sum(1 for w in boundary_kws if w in content) >= 1
    confidence_ok= any(w in content for w in ["置信度","高","中","低"])
    return {
        "file_created":          1.0,
        "has_three_decisions":   1.0 if has_three else 0.0,
        "boundary_respected":    1.0 if boundary_ok else 0.0,
        "has_confidence_levels": 1.0 if confidence_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 判断是否符合 value_map 的逻辑 · 理由是否有陈默式论证 · 边界情境是否正确降级判断是否符合 value_map 的逻辑 · 理由是否有陈默式论证 · 边界情境是否正确降级

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
