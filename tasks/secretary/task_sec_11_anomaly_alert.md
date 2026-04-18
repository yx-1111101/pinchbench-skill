---
id: task_sec_11_anomaly_alert
name: "主动情报 · 异常监控告警"
category: secretary
grading_type: automated
timeout_seconds: 540
workspace_files: []
dataset_dir: dataset/secretary/task_sec_11_anomaly_alert
---

## Prompt

请设置一个异常监控规则：

**监控目标**：「开心项目」飞书群
**触发条件**：该群超过 24 小时没有任何新消息
**触发动作**：通过 IM 向我发送提醒，内容包含：
- 群名称
- 最后一条消息的时间
- 提醒文案：「⚠️ 开心项目群已超过24小时无消息，请确认项目进展」

将监控规则的配置信息保存到 `monitor_setup.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：monitor_setup.txt 是否存在
- `file_not_empty`：内容非空
- `mentions_target`：包含监控目标（「开心项目」）
- `mentions_condition`：包含触发条件（「24」+「小时」或「无消息」）
- `mentions_action`：包含告警动作（「发送」「通知」「提醒」）

## Grading Criteria

- [ ] file_created: monitor_setup.txt 是否存在
- [ ] file_not_empty: 内容非空
- [ ] mentions_target: 包含监控目标（「开心项目」）
- [ ] mentions_condition: 包含触发条件（「24」+「小时」或「无消息」）
- [ ] mentions_action: 包含告警动作（「发送」「通知」「提醒」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "monitor_setup.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_target","mentions_condition","mentions_action"]}
    content = f.read_text(encoding="utf-8").strip()
    mentions_target = "开心项目" in content
    mentions_condition = "24" in content and any(w in content for w in ["小时","hour","无消息","没有消息"])
    mentions_action = any(w in content for w in ["发送","通知","提醒","alert","notify"])
    return {
        "file_created":      1.0,
        "file_not_empty":    1.0 if len(content) > 0 else 0.0,
        "mentions_target":   1.0 if mentions_target else 0.0,
        "mentions_condition":1.0 if mentions_condition else 0.0,
        "mentions_action":   1.0 if mentions_action else 0.0,
    }
```
