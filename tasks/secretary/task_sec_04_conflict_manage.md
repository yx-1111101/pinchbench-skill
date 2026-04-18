---
id: task_sec_04_conflict_manage
name: "飞书日程冲突处理（自动避让创建）"
category: secretary
grading_type: automated
timeout_seconds: 360
workspace_files: []
dataset_dir: dataset/secretary/task_sec_04_conflict_manage
---

## 前置条件

- 运行环境已接入 **飞书日历**（开放平台日历 API、飞书应用机器人，或已登录的飞书客户端自动化）。
- 该任务要求 **真实调用飞书日历** 完成查询与创建，不接受仅写本地结果文件但未实际创建日程的替代方案。
- 评测环境中，用户请求的原始时段会与已有飞书日程冲突；代理需要先检查日历占用，再选择一个同日下午的可用两小时时段完成创建。

## Prompt

帮我在 **飞书日历** 里安排一场「投资人沟通会」，优先放在 **下周一下午 14:00-16:00**，时长 **两小时**。如果该时段冲突，请你先检查我的飞书日历，再自动改到 **同一天下午** 的其他可用两小时时段，并把最终创建结果保存到工作区根目录的 `calendar_result.txt`。

`calendar_result.txt` 至少需要包含：

- 会议标题
- 原始请求时段
- 最终安排日期
- 最终开始时间
- 最终结束时间
- 冲突说明
- 飞书日历创建确认信息（如 `event_id`、日程链接、飞书返回的确认字段）

## Expected Behavior

The agent should complete the task as described in the prompt.

代理应在单轮内完成该任务：先检查飞书日历中下周一下午 `14:00-16:00` 是否被占用；若冲突，则自动选择同一天下午的其他可用两小时时段，并通过飞书日历完成真实创建。`calendar_result.txt` 必须记录原始请求时段、冲突说明、最终时段与真实创建返回的可核对信息。评测不要求再次询问用户确认，也不要求多轮对话。

Evaluation criteria:
- `file_created`：`calendar_result.txt` 是否存在
- `file_not_empty`：文件内容非空
- `mentions_title`：结果中包含「投资人沟通会」
- `mentions_requested_slot`：结果中包含原始请求时段 `14:00-16:00`
- `mentions_conflict`：结果中明确说明原始时段存在冲突
- `mentions_rescheduled_slot`：结果中包含一个不同于 `14:00-16:00` 的最终下午时间段
- `mentions_feishu`：结果中包含飞书/Lark/日历创建确认信息
- `has_creation_proof`：结果中包含可核对的真实创建凭据（如 `event_id`、日程链接、`calendar_id` 等）

## Grading Criteria

- [ ] file_created: `calendar_result.txt` 是否存在
- [ ] file_not_empty: 文件内容非空
- [ ] mentions_title: 结果中包含「投资人沟通会」
- [ ] mentions_requested_slot: 结果中包含原始请求时段 `14:00-16:00`
- [ ] mentions_conflict: 结果中明确说明原始时段存在冲突
- [ ] mentions_rescheduled_slot: 结果中包含一个不同于 `14:00-16:00` 的最终下午时间段
- [ ] mentions_feishu: 结果中包含飞书/Lark/日历创建确认信息
- [ ] has_creation_proof: 结果中包含可核对的真实创建凭据（如 `event_id`、日程链接、`calendar_id`）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    import re
    workspace_path = Path(workspace_path)

    def _flatten(node):
        parts = []
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, dict):
            for value in node.values():
                parts.extend(_flatten(value))
        elif isinstance(node, list):
            for value in node:
                parts.extend(_flatten(value))
        return parts

    transcript_text = "\n".join(_flatten(transcript))
    tl = transcript_text.lower()
    f = workspace_path / "calendar_result.txt"
    if not f.exists():
        return {
            k: 0.0
            for k in [
                "file_created",
                "file_not_empty",
                "mentions_title",
                "mentions_requested_slot",
                "mentions_conflict",
                "mentions_rescheduled_slot",
                "mentions_feishu",
                "has_creation_proof",
            ]
        }

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    cl = content.lower()
    mentions_title = "投资人沟通会" in content
    mentions_requested_slot = any(w in content for w in ["14:00-16:00", "14:00 - 16:00", "14点到16点", "14点-16点"])
    mentions_conflict = any(w in content for w in ["冲突", "占用", "已有日程", "已有会议", "重叠"]) or (
        any(w in transcript_text for w in ["冲突", "占用", "已有日程", "已有会议", "重叠"]) or "conflict" in tl
    )
    mentions_rescheduled_slot = (
        any(w in content for w in ["13:00-15:00", "15:00-17:00", "16:00-18:00", "13:00 - 15:00", "15:00 - 17:00", "16:00 - 18:00"])
        or bool(re.search(r"(13|15|16):00\s*[-~]\s*(15|17|18):00", content))
    )
    mentions_feishu = any(w in content for w in ["飞书", "Feishu", "Lark", "event_id", "日历链接", "calendar"]) or (
        "feishu" in cl or "lark" in cl or "event_id" in cl or "calendar" in cl
    )
    has_creation_proof = any(w in content for w in ["event_id", "calendar_id", "https://", "http://", "日历链接", "event id"]) or (
        "event_id" in cl or "calendar_id" in cl or "event id" in cl
    )
    return {
        "file_created": 1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "mentions_title": 1.0 if mentions_title else 0.0,
        "mentions_requested_slot": 1.0 if mentions_requested_slot else 0.0,
        "mentions_conflict": 1.0 if mentions_conflict else 0.0,
        "mentions_rescheduled_slot": 1.0 if mentions_rescheduled_slot else 0.0,
        "mentions_feishu": 1.0 if mentions_feishu else 0.0,
        "has_creation_proof": 1.0 if has_creation_proof else 0.0,
    }
```
