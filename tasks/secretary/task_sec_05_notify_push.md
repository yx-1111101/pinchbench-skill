---
id: task_sec_05_notify_push
name: "通知主动推送"
category: secretary
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/secretary/task_sec_05_notify_push
---

## Prompt

请通过飞书向我发送以下会议提醒消息，并将发送结果保存到 `notify_result.txt`：

消息内容：
```
⏰ 会议提醒
【Q2产品规划对齐会】将在30分钟后开始
时间：14:00 - 15:30
地点：会议室B
参会人：张伟、李娜、王芳
请提前准备Q2 OKR草稿
```

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：notify_result.txt 是否存在
- `file_not_empty`：内容非空
- `mentions_success`：结果中包含发送成功相关词（「已发送」「success」「sent」「成功」）
- `mentions_channel`：结果中包含渠道信息（「飞书」「Feishu」）

## Grading Criteria

- [ ] file_created: notify_result.txt 是否存在
- [ ] file_not_empty: 内容非空
- [ ] mentions_success: 结果中包含发送成功相关词（「已发送」「success」「sent」「成功」）
- [ ] mentions_channel: 结果中包含渠道信息（「飞书」「Feishu」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "notify_result.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_success","mentions_channel"]}
    content = f.read_text(encoding="utf-8").strip()
    mentions_success = any(w in content.lower() for w in ["已发送","success","sent","成功","发送成功"])
    mentions_channel = any(w in content for w in ["飞书","Feishu"])
    return {
        "file_created":    1.0,
        "file_not_empty":  1.0 if len(content) > 0 else 0.0,
        "mentions_success":1.0 if mentions_success else 0.0,
        "mentions_channel":1.0 if mentions_channel else 0.0,
    }
```
