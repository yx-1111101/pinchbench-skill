---
id: task_f_04_speech_to_text
name: "task_f_04_speech_to_text"
category: foundation
grading_type: automated
timeout_seconds: 90
workspace_files:
  - audio.wav
dataset_dir: dataset/foundation/task_f_04_speech_to_text
---

## Prompt

工作区有一段音频 `audio.wav`（内容：一段语音）。

请将音频转录为文字，保存到 `transcript.txt`。

## Expected Behavior

The agent should transcribe `audio.wav` accurately. The grader compares `transcript.txt` against **ground-truth phrase groups** derived from the dataset audio (see `dataset/.../golden_transcript.txt` in the repo for reference only; that file is **not** placed in the agent workspace).

Evaluation criteria:
- `file_created`: transcript.txt 是否存在
- `keyword_hit_rate`: 转录命中金标关键词组的比例（0–1）

## Grading Criteria

- [ ] file_created: transcript.txt 是否存在
- [ ] keyword_hit_rate: 命中金标关键词组比例（见 `golden_transcript.txt` / GROUND_TRUTH_KEYWORDS）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "transcript.txt"
    if not f.exists():
        return {"file_created": 0.0, "keyword_hit_rate": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    refusal_phrases = [
        "无法识别", "无法处理", "无法转写", "听不到", "不能识别", "不支持音频",
        "cannot recognize", "cannot process", "i cannot hear", "i'm unable to",
        "no audio", "cannot transcribe", "unable to process", "can't process the audio",
    ]
    if any((p in content) or (p in c_lower) for p in refusal_phrases):
        return {"file_created": 1.0, "keyword_hit_rate": 0.0}

    # Phrases aligned with dataset golden_transcript.txt / audio content
    GROUND_TRUTH_KEYWORDS = [
        ("早上好",),
        ("新的一天",),
        ("好心情",),
        ("祝你",),
    ]

    hits = sum(
        1 for synonyms in GROUND_TRUTH_KEYWORDS
        if any(s in content for s in synonyms)
    )
    hit_rate = hits / len(GROUND_TRUTH_KEYWORDS)

    return {
        "file_created": 1.0,
        "keyword_hit_rate": round(hit_rate, 2),
    }
```
