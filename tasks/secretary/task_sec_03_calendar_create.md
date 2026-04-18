---
id: task_sec_03_calendar_create
name: "飞书日程创建"
category: secretary
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/secretary/task_sec_03_calendar_create
---

## 前置条件

- 运行环境已接入 **飞书日历**（开放平台日历 API、飞书应用机器人，或已登录的飞书客户端自动化）。
- 该任务要求 **真实调用飞书日历** 完成创建，不接受仅写本地结果文件但未实际创建日程的替代方案。

## Prompt

请根据以下信息，在 **我的飞书日历** 中创建一个会议日程，并将创建结果（事件 ID、`event_id`、日程链接或飞书返回的确认信息）保存到工作区根目录的 `calendar_result.txt`：

- 标题：Q2产品规划对齐会
- 时间：下周一 14:00 - 15:30
- 参会人：张伟、李娜、王芳
- 地点：会议室B
- 备注：请提前准备Q2 OKR草稿

创建时请通过飞书日历侧完成参会人邀请与会议室/备注字段的写入（与飞书日程表单字段一致即可）。

## Expected Behavior

The agent should complete the task as described in the prompt.

代理应真实调用飞书日历创建流程，并在 `calendar_result.txt` 中留下可核对的信息（非空文本）。

Evaluation criteria:
- `file_created`：`calendar_result.txt` 是否存在于工作区根目录
- `file_not_empty`：文件内容非空
- `mentions_title`：结果中包含「Q2」或「规划」（证明标题写入成功）
- `mentions_time`：结果中包含时间相关信息（「14」或「下周」或「monday」）
- `mentions_feishu`：结果中体现飞书或 Lark 渠道（「飞书」「Feishu」「Lark」或大小写不敏感的 `feishu` / `lark`）
- `has_creation_proof`：结果中包含真实创建凭据（如 `event_id`、`calendar_id`、日程链接）

## Grading Criteria

- [ ] file_created: calendar_result.txt 是否存在
- [ ] file_not_empty: 文件内容非空
- [ ] mentions_title: 结果中包含「Q2」或「规划」（证明标题写入成功）
- [ ] mentions_time: 结果中包含时间相关信息（「14」或「下周」或「monday」）
- [ ] mentions_feishu: 结果中体现飞书/Lark 渠道或明确的飞书日程创建反馈
- [ ] has_creation_proof: 结果中包含真实创建凭据（如 `event_id`、`calendar_id`、日程链接）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "calendar_result.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_title","mentions_time","mentions_feishu","has_creation_proof"]}
    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    cl = content.lower()
    mentions_title = any(w in content for w in ["Q2","规划","q2"])
    mentions_time = any(w in content for w in ["14","下周","monday","Monday","14:00"])
    mentions_feishu = any(w in content for w in ["飞书","Feishu","Lark","lark"]) or (
        "feishu" in cl or "lark" in cl
    )
    has_creation_proof = any(w in content for w in ["event_id","calendar_id","https://","http://","日程链接","event id"]) or (
        "event_id" in cl or "calendar_id" in cl or "event id" in cl
    )
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "mentions_title": 1.0 if mentions_title else 0.0,
        "mentions_time":  1.0 if mentions_time else 0.0,
        "mentions_feishu": 1.0 if mentions_feishu else 0.0,
        "has_creation_proof": 1.0 if has_creation_proof else 0.0,
    }
```
