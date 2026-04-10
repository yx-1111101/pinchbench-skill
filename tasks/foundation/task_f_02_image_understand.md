---
id: task_f_02_image_understand
name: "task_f_02_image_understand"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_02_image_understand
---

## Prompt

工作区有一张图片 `test_image.png`

请描述图片内容，保存到 `description.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: description.txt 是否存在
- `has_description`: 是否产出了实质性的图片描述（非空、且非「无法识别」等拒绝类回复）

## Grading Criteria

- [ ] file_created: description.txt 是否存在
- [ ] has_description: 是否产出了实质性的图片描述（非空、且非「无法识别」等拒绝类回复）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "description.txt"
    if not f.exists():
        return {"file_created": 0.0, "has_description": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    # 拒绝/无法识别类回复不算「有描述」
    refusal_phrases = [
        "无法识别", "无法辨认", "看不到", "不能识别", "无法看到", "没有图片",
        "cannot recognize", "i cannot see", "i'm unable to", "i don't have",
        "no image", "cannot view", "unable to identify", "can't see the image",
    ]
    is_refusal = any((p in content) or (p in c_lower) for p in refusal_phrases)

    has_description = len(content) > 10 and not is_refusal

    return {
        "file_created": 1.0,
        "has_description": 1.0 if has_description else 0.0,
    }
```
