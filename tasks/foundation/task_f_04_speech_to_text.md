---
id: task_f_04_speech_to_text
name: "task_f_04_speech_to_text"
category: foundation
grading_type: automated
timeout_seconds: 90
workspace_files: []
dataset_dir: dataset/foundation/task_f_04_speech_to_text
---

## Prompt

工作区有一段音频 `audio.wav`（内容：一段语音）。

请将音频转录为文字，保存到 `transcript.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: transcript.txt 是否存在
- `has_content`: 是否产出了实质性转录（非空、且非「无法识别/无法处理音频」等拒绝类回复）

## Grading Criteria

- [ ] file_created: transcript.txt 是否存在
- [ ] has_content: 是否产出了实质性转录（非空、且非「无法识别/无法处理音频」等拒绝类回复）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "transcript.txt"
    if not f.exists():
        return {"file_created": 0.0, "has_content": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    refusal_phrases = [
        "无法识别", "无法处理", "无法转写", "听不到", "不能识别", "不支持音频",
        "cannot recognize", "cannot process", "i cannot hear", "i'm unable to",
        "no audio", "cannot transcribe", "unable to process", "can't process the audio",
    ]
    is_refusal = any((p in content) or (p in c_lower) for p in refusal_phrases)

    has_content = len(content) > 20 and not is_refusal

    return {
        "file_created": 1.0,
        "has_content": 1.0 if has_content else 0.0,
    }
```
