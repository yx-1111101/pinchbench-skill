---
id: task_sec_09_browser_op
name: "浏览器操作"
category: secretary
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/secretary/task_sec_09_browser_op
---

## Prompt

请通过浏览器，将我的飞书状态修改为「休息中」，并将操作结果（截图路径或操作确认）保存到 `browser_result.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：browser_result.txt 是否存在
- `file_not_empty`：内容非空
- `mentions_success`：结果中包含操作成功相关词（「休息中」「已设置」「success」「成功」）
- `screenshot_saved`：workspace 中是否存在截图文件（.png / .jpg）

## Grading Criteria

- [ ] file_created: browser_result.txt 是否存在
- [ ] file_not_empty: 内容非空
- [ ] mentions_success: 结果中包含操作成功相关词（「休息中」「已设置」「success」「成功」）
- [ ] screenshot_saved: workspace 中是否存在截图文件（.png / .jpg）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "browser_result.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_success","screenshot_saved"]}
    content = f.read_text(encoding="utf-8").strip()
    mentions_success = any(w in content for w in ["休息中","已设置","success","成功","设置成功"])
    screenshots = list(workspace_path.glob("*.png")) + list(workspace_path.glob("*.jpg"))
    return {
        "file_created":    1.0,
        "file_not_empty":  1.0 if len(content) > 0 else 0.0,
        "mentions_success":1.0 if mentions_success else 0.0,
        "screenshot_saved":1.0 if len(screenshots) > 0 else 0.0,
    }
```
