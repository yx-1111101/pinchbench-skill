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

请通过浏览器访问公开网页 [https://www.apple.com](https://www.apple.com)，完成以下操作，并将结果保存到 `browser_result.txt`：

- 记录页面标题
- 记录当前访问的 URL
- 保存一张页面截图到工作区（`.png` 或 `.jpg`）
- 在 `browser_result.txt` 中写明操作已完成，并注明截图文件名

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：browser_result.txt 是否存在
- `file_not_empty`：内容非空
- `mentions_page_info`：结果中包含页面标题或 URL 信息
- `screenshot_saved`：workspace 中是否存在截图文件（.png / .jpg）

## Grading Criteria

- [ ] file_created: browser_result.txt 是否存在
- [ ] file_not_empty: 内容非空
- [ ] mentions_page_info: 结果中包含页面标题或 URL 信息
- [ ] screenshot_saved: workspace 中是否存在截图文件（.png / .jpg）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "browser_result.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_page_info","screenshot_saved"]}
    content = f.read_text(encoding="utf-8").strip()
    mentions_page_info = any(w in content for w in ["Apple","apple.com","页面标题","URL","网址"])
    screenshots = list(workspace_path.glob("*.png")) + list(workspace_path.glob("*.jpg"))
    return {
        "file_created":      1.0,
        "file_not_empty":    1.0 if len(content) > 0 else 0.0,
        "mentions_page_info":1.0 if mentions_page_info else 0.0,
        "screenshot_saved":  1.0 if len(screenshots) > 0 else 0.0,
    }
```
