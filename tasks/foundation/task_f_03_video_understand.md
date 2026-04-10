---
id: task_f_03_video_understand
name: "task_f_03_video_understand"
category: foundation
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/foundation/task_f_03_video_understand
---

## Prompt

工作区有一段的视频 `demo.mp4`

请生成视频摘要，保存到 `video_summary.txt`，要求：
- 说明视频主要内容

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: video_summary.txt 是否存在
- `has_content`: 是否产出了实质性视频摘要（非空、且非「无法识别/无法处理视频」等拒绝类回复；不区分能力来自模型本身还是工具）

## Grading Criteria

- [ ] file_created: video_summary.txt 是否存在
- [ ] has_content: 是否产出了实质性视频摘要（非空、且非「无法识别/无法处理视频」等拒绝类回复；不区分能力来自模型本身还是工具）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "video_summary.txt"
    if not f.exists():
        return {"file_created": 0.0, "has_content": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    refusal_phrases = [
        "无法识别", "无法辨认", "无法处理", "无法分析", "无法读取", "无法打开", "无法访问",
        "看不到", "不能识别", "不支持视频", "没有视频", "未提供视频", "找不到视频",
        "cannot recognize", "cannot process", "cannot analyze", "cannot view",
        "cannot read", "cannot open", "cannot access",
        "i cannot see", "i'm unable to", "i don't have",
        "no video", "can't process the video", "can't see the video",
    ]
    is_refusal = any((p in content) or (p in c_lower) for p in refusal_phrases)

    # 拒绝/无法访问类回复不算「有摘要」；过短内容（例如一句话借口）也不算
    has_content = len(content) > 10 and not is_refusal

    return {
        "file_created": 1.0,
        "has_content": 1.0 if has_content else 0.0,
    }
```
