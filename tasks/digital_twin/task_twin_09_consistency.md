---
id: task_twin_09_consistency
name: "质量验证 — 同一问题问两次，验证分身稳定性"
category: digital_twin
grading_type: llm_judge
timeout_seconds: 540
workspace_files:
  - persona.json
dataset_dir: dataset/digital_twin/task_twin_09_consistency
---

## Prompt

工作区有陈默的完整人格档案 `persona.json`。

请基于该档案，对以下问题回答**两次**（模拟两个独立会话），保存到 `consistency_test.md`：

**问题**：「有人想和陈默合作做付费社群，月费99元，目标1000人，对方负责运营，陈默只需每月直播2次。陈默会接受吗？为什么？」

格式：
```markdown
# 问题
<原问题>

## 第一次回答
<回答内容>

## 第二次回答
<回答内容>

## 一致性自评
- 核心判断是否一致：
- 理由是否一致：
- 若有差异，差异在哪里：
```

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：consistency_test.md 存在
- `has_two_answers`：包含两次回答
- `has_self_eval`：包含一致性自评

**LLM Judge**：两次核心判断是否一致 · 理由是否基于同样逻辑 · 自评是否诚实准确

## Grading Criteria

- [ ] file_created: consistency_test.md 存在
- [ ] has_two_answers: 包含两次回答
- [ ] has_self_eval: 包含一致性自评

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "consistency_test.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_two_answers","has_self_eval"]}
    content = f.read_text(encoding="utf-8")
    has_two  = "第一次回答" in content and "第二次回答" in content
    has_eval = any(w in content for w in ["一致性","自评","差异","一致","不同"])
    return {
        "file_created":   1.0,
        "has_two_answers":1.0 if has_two else 0.0,
        "has_self_eval":  1.0 if has_eval else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 两次核心判断是否一致 · 理由是否基于同样逻辑 · 自评是否诚实准确

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
