---
id: task_sec_10_daily_digest
name: "定时摘要推送"
category: secretary
grading_type: automated
timeout_seconds: 540
workspace_files: []
dataset_dir: dataset/secretary/task_sec_10_daily_digest
---

## Prompt

请设置一个定时任务：**每天早上 9:00**，自动收集以下信息并通过飞书推送给我：

1. 今日日历事项
2. 未读重要消息摘要
3. 今日值得关注的行业资讯（联网搜索）

将定时任务的配置信息和一次立即执行的测试结果保存到 `digest_setup.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：digest_setup.txt 是否存在
- `file_not_empty`：内容非空
- `cron_configured`：轨迹中出现创建/查看/写入 cron、crontab、launchd 等定时任务配置行为
- `test_sent`：包含发送确认词（「已发送」「sent」「success」「成功」）

## Grading Criteria

- [ ] file_created: digest_setup.txt 是否存在
- [ ] file_not_empty: 内容非空
- [ ] cron_configured: 轨迹中出现创建/查看/写入 cron、crontab、launchd 等定时任务配置行为
- [ ] test_sent: 包含发送确认词（「已发送」「sent」「success」「成功」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "digest_setup.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","cron_configured","test_sent"]}
    content = f.read_text(encoding="utf-8").strip()
    transcript_text = str(transcript or "")
    cron_patterns = [
        r'crontab',
        r'\bcron\b',
        r'launchctl',
        r'launchd',
        r'/etc/crontab',
        r'cron\.d',
        r'plist',
        r'0\s+9\s+\*\s+\*\s+\*',
    ]
    cron_ok = any(re.search(p, transcript_text, re.I) for p in cron_patterns)
    sent_ok = any(w in content.lower() for w in ["已发送","sent","success","成功","发送成功"])
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "cron_configured":1.0 if cron_ok else 0.0,
        "test_sent":      1.0 if sent_ok else 0.0,
    }
```
