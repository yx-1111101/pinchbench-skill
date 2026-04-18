---
id: task_f_09_dialog_logging
name: "task_f_09_dialog_logging"
category: foundation
grading_type: automated
timeout_seconds: 360
workspace_files: []
dataset_dir: dataset/foundation/task_f_09_dialog_logging
---

## Prompt

这是一个**多轮对话记录测试**（纯文本任务，不涉及语音 I/O）。

请模拟一段 3 轮对话，并将每轮的用户输入和 Agent 回复记录到 `dialog_log.txt`：

- 轮次 1：用户问「今天天气怎么样」
- 轮次 2：用户问「需要带伞吗」
- 轮次 3：用户说「谢谢」

要求：
- 必须包含 3 个轮次
- 每个轮次都要有「用户」与「Agent」两侧内容
- 回复需与该轮用户输入语义相关

## Expected Behavior

The task evaluates multi-turn conversational handling and structured dialogue logging in plain text. It does not test speech recognition or speech synthesis. Grading checks round completeness and response relevance per round.

Evaluation criteria:
- `file_created`: dialog_log.txt 是否存在
- `round_count_ok`: 是否包含 3 个轮次
- `user_utterance_hit_rate`: 三轮用户输入要点命中比例（0–1）
- `agent_response_hit_rate`: 三轮 Agent 回复语义相关命中比例（0–1）

## Grading Criteria

- [ ] file_created: dialog_log.txt 是否存在
- [ ] round_count_ok: 是否包含 3 个轮次
- [ ] user_utterance_hit_rate: 用户输入要点命中率
- [ ] agent_response_hit_rate: Agent 回复语义相关命中率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    import re
    workspace_path = Path(workspace_path)
    f = workspace_path / "dialog_log.txt"
    if not f.exists():
        return {
            "file_created": 0.0,
            "round_count_ok": 0.0,
            "user_utterance_hit_rate": 0.0,
            "agent_response_hit_rate": 0.0,
        }

    c = f.read_text(encoding="utf-8", errors="ignore")
    cl = c.lower()

    # User-side cues that should appear across rounds
    USER_GROUPS = [
        ("天气", "weather"),
        ("伞",),
        ("谢谢", "感谢"),
    ]
    user_hits = sum(
        1
        for syns in USER_GROUPS
        if any((s in c) or (s in cl) for s in syns)
    )
    user_hit_rate = user_hits / len(USER_GROUPS)

    # Agent-side relevance cues: weather response, umbrella advice, polite close
    AGENT_GROUPS = [
        ("晴", "雨", "多云", "天气", "weather", "温度"),
        ("伞", "带伞", "不用带伞", "umbrella"),
        ("不客气", "很高兴", "祝你", "you are welcome", "welcome"),
    ]
    agent_hits = sum(
        1
        for syns in AGENT_GROUPS
        if any((s in c) or (s in cl) for s in syns)
    )
    agent_hit_rate = agent_hits / len(AGENT_GROUPS)

    # Count explicit round markers; fallback to user turns
    round_markers = len(re.findall(r"轮次\\s*[：: ]?\\d+", c))
    if round_markers == 0:
        round_markers = len(re.findall(r"(用户[：:])|(user[：:])", cl))

    return {
        "file_created": 1.0,
        "round_count_ok": 1.0 if round_markers >= 3 else 0.0,
        "user_utterance_hit_rate": round(user_hit_rate, 2),
        "agent_response_hit_rate": round(agent_hit_rate, 2),
    }
```
