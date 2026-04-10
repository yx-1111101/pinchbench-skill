---
id: task_f_09_realtime_voice
name: "task_f_09_realtime_voice"
category: foundation
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/foundation/task_f_09_realtime_voice
---

## Prompt

模拟一段 3 轮语音对话，将每轮的用户输入和 Agent 回复记录到 `voice_log.txt`：

- 轮次 1：用户问「今天天气怎么样」
- 轮次 2：用户问「需要带伞吗」
- 轮次 3：用户说「谢谢」

## Expected Behavior

The agent should complete the task as described in the prompt.

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "voice_log.txt"
    if not f.exists(): return {"file_created":0.0,"has_3_rounds":0.0}
    c = f.read_text(encoding="utf-8",errors="ignore")
    rounds = c.count("轮次") or c.count("Round") or c.count("用户：")
    return {"file_created":1.0,"has_3_rounds":1.0 if rounds>=3 else 0.0}
```
