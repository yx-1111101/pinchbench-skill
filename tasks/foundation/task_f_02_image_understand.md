---
id: task_f_02_image_understand
name: "task_f_02_image_understand"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files:
  - test_image.png
dataset_dir: dataset/foundation/task_f_02_image_understand
---

## Prompt

工作区有一张图片 `test_image.png`

请描述图片内容，保存到 `description.txt`。

## Expected Behavior

The agent should open `test_image.png`, accurately describe its visual content, and write the description to `description.txt`.

The image contains specific verifiable elements (defined in `GROUND_TRUTH_KEYWORDS` below). A correct description must mention enough of these elements to demonstrate the model actually perceived the image, rather than fabricating plausible-sounding content.

Evaluation criteria:
- `file_created`: description.txt 是否存在
- `keyword_hit_rate`: 描述中命中图片 ground-truth 关键词组的比例（0–1，每组任一同义词命中计 1 组）

## Grading Criteria

- [ ] file_created: description.txt 是否存在
- [ ] keyword_hit_rate: ground-truth 关键词组命中率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "description.txt"
    if not f.exists():
        return {"file_created": 0.0, "keyword_hit_rate": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    # Ground-truth keywords derived from the actual image content.
    # Image: an orange/ginger kitten standing on a windowsill, looking outside.
    # Each entry is a tuple of synonyms; a tuple counts as one hit if ANY synonym matches.
    GROUND_TRUTH_KEYWORDS = [
        ("cat", "kitten", "猫", "小猫", "猫咪"),
        ("orange", "ginger", "橘", "橙", "黄", "姜黄"),
        ("window", "windowsill", "窗", "窗台", "窗户"),
        ("looking", "gazing", "staring", "望", "看", "眺望", "凝视"),
        ("outdoor", "outside", "树", "tree", "sky", "天空", "绿", "green"),
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
