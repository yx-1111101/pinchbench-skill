---
id: task_sec_07_email_search
name: "邮件检索"
category: secretary
grading_type: hybrid
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/secretary/task_sec_07_email_search
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

请在我的邮箱中搜索：**「开心项目组」在过去7天内发给我的会议纪要邮件**，找到后：

1. 将邮件主题、发件人、发送时间列出来
2. 提取邮件中的待办事项
3. 保存到 `email_search_result.md`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：email_search_result.md 是否存在
- `file_not_empty`：内容非空
- `has_email_meta`：是否包含主题/发件人/时间等元信息
- `has_action_items`：是否提取了待办事项

**LLM Judge**：检索结果相关性 · 信息提取完整度

## Grading Criteria

- [ ] file_created: email_search_result.md 是否存在
- [ ] file_not_empty: 内容非空
- [ ] has_email_meta: 是否包含主题/发件人/时间等元信息
- [ ] has_action_items: 是否提取了待办事项

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "email_search_result.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_email_meta","has_action_items"]}
    content = f.read_text(encoding="utf-8").strip()
    has_meta = any(w in content for w in ["主题","发件人","时间","subject","from","date","Subject","From","Date"])
    has_actions = any(w in content for w in ["待办","action","todo","TODO","跟进","负责"])
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "has_email_meta": 1.0 if has_meta else 0.0,
        "has_action_items":1.0 if has_actions else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 检索结果相关性 · 信息提取完整度检索结果相关性 · 信息提取完整度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
