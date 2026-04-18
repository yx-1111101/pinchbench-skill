---
id: task_sec_07_email_search
name: "邮件检索"
category: secretary
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - emails.json
dataset_dir: dataset/secretary/task_sec_07_email_search
grading_weights:
  automated: 0.7
  llm_judge: 0.3
---

## Prompt

工作区有一个文件：
- `emails.json`：本地导出的邮件数据

请在这些邮件中搜索：**「开心项目组」在过去 7 天内发给我的会议纪要邮件**。

为避免歧义，检索时请以 **2026-04-13 00:00:00** 为“当前时间”。

找到目标邮件后：

1. 将邮件主题、发件人、发送时间列出来
2. 提取邮件中的待办事项
3. 保存到 `email_search_result.md`

请基于数据集中的真实内容作答，不要编造不存在的邮件。

## Expected Behavior

The agent should inspect the provided local email dataset, identify the correct message that matches sender and time constraints, extract the requested metadata and action items, and save the result to `email_search_result.md`.

Evaluation criteria:
**自动**：
- `file_created`：email_search_result.md 是否存在
- `file_not_empty`：内容非空
- `matched_target_email`：是否命中正确邮件
- `extracted_key_actions`：是否提取出关键待办事项

**LLM Judge**：检索过程合理性 · 信息提取完整度

## Grading Criteria

- [ ] file_created: email_search_result.md 是否存在
- [ ] file_not_empty: 内容非空
- [ ] matched_target_email: 是否命中正确邮件
- [ ] extracted_key_actions: 是否提取出关键待办事项

## Automated Checks

```python
def grade(transcript, workspace_path):
    import re
    from pathlib import Path

    workspace_path = Path(workspace_path)
    f = workspace_path / "email_search_result.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created", "file_not_empty", "matched_target_email", "extracted_key_actions"]}

    content = f.read_text(encoding="utf-8").strip()

    normalized = re.sub(r"\s+", "", content.lower())

    expected_subject = "开心项目组周会会议纪要（2026-04-10）"
    expected_sender = "开心项目组 <team@happyproject.example.com>"
    expected_date = "2026-04-10 09:30:00"

    matched_target_email = all(
        token in content
        for token in [expected_subject, expected_sender, expected_date]
    )

    action_hits = 0
    action_groups = [
        ["李娜", "视觉稿"],
        ["王强", "埋点方案"],
        ["陈晨", "用户访谈摘要"],
    ]
    for group in action_groups:
        if all(token.replace(" ", "").lower() in normalized for token in group):
            action_hits += 1

    return {
        "file_created": 1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "matched_target_email": 1.0 if matched_target_email else 0.0,
        "extracted_key_actions": 1.0 if action_hits >= 2 else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 检索结果相关性 · 信息提取完整度 · 是否严格基于数据集作答

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
