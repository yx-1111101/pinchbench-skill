---
id: task_f_03_video_understand
name: "task_f_03_video_understand"
category: foundation
grading_type: automated
timeout_seconds: 360
workspace_files:
  - demo.mp4
dataset_dir: dataset/foundation/task_f_03_video_understand
---

## Prompt

工作区有一段视频 `demo.mp4`

请生成视频摘要，保存到 `video_summary.txt`，要求：
- 说明视频主要内容

## Expected Behavior

The agent should process `demo.mp4` (via vision capabilities or tools), accurately summarize what is visible, and write the summary to `video_summary.txt`.

The video contains specific verifiable elements (defined in `GROUND_TRUTH_KEYWORDS` below). A correct summary must mention enough of these elements to show the model actually perceived the video, rather than fabricating plausible-sounding content.

Evaluation criteria:
- `file_created`: video_summary.txt 是否存在
- `keyword_hit_rate`: 摘要中命中 ground-truth 关键词组的比例（每组任一同义词命中即计 1 组）

## Grading Criteria

- [ ] file_created: video_summary.txt 是否存在
- [ ] keyword_hit_rate: 关键词组命中率（与 `demo.mp4` 画面对应，见 Automated Checks）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "video_summary.txt"
    if not f.exists():
        return {"file_created": 0.0, "keyword_hit_rate": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    # Ground-truth keywords derived from the actual video content (demo.mp4).
    # Scene: orange tabby cat on a white windowsill, looking toward the camera;
    # window and soft outdoor greenery/sky visible in the background.
    # Each tuple is one keyword group; ANY synonym match counts as one hit for that group.
    GROUND_TRUTH_KEYWORDS = [
        ("cat", "kitten", "猫", "小猫", "猫咪"),
        ("orange", "ginger", "tabby", "橘", "橙", "黄", "姜黄", "虎斑"),
        ("window", "windowsill", "窗", "窗台", "窗户"),
        ("looking", "gazing", "staring", "看", "望", "注视", "凝视", "镜头", "camera"),
        ("outdoor", "outside", "树", "tree", "sky", "天空", "绿", "green", "blur", "模糊"),
    ]

    hits = sum(
        1 for synonyms in GROUND_TRUTH_KEYWORDS
        if any(s in c_lower for s in synonyms)
    )
    hit_rate = hits / len(GROUND_TRUTH_KEYWORDS)

    return {
        "file_created": 1.0,
        "keyword_hit_rate": round(hit_rate, 2),
    }
```
