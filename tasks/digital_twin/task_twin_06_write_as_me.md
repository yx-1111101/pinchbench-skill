---
id: task_twin_06_write_as_me
name: "调用执行 — 以用户风格创作文章"
category: digital_twin
grading_type: llm_judge
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/digital_twin/task_twin_06_write_as_me
---

## Prompt

工作区有陈默的风格指南 `style_guide.md` 和写作委托 `writing_brief.txt`。

**委托**：以陈默名义写一篇朋友圈长文（300-500字），主题：「我为什么最近开始减少开会频率」

将文章保存到 `ghost_article.md`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：ghost_article.md 存在
- `length_ok`：字数在 200-600 字之间

**LLM Judge**（权重更高）：是否体现 style_guide 的写作规则 · 是否有 AI 腔 · 论点是否有数字或案例支撑

## Grading Criteria

- [ ] file_created: ghost_article.md 存在
- [ ] length_ok: 字数在 200-600 字之间

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "ghost_article.md"
    if not f.exists():
        return {"file_created": 0.0, "length_ok": 0.0}
    content = f.read_text(encoding="utf-8").strip()
    char_count = len(content.replace(" ","").replace("\n",""))
    return {
        "file_created": 1.0,
        "length_ok":    1.0 if 200 <= char_count <= 600 else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**（权重更高）：是否体现 style_guide 的写作规则 · 是否有 AI 腔 · 论点是否有数字或案例支撑

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
