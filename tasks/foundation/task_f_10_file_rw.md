---
id: task_f_10_file_rw
name: "task_f_10_file_rw"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_10_file_rw
---

## Prompt

请完成以下三步文件操作：

1. 创建文件 `note.txt`，写入内容：「第一次写入」
2. 读取 `note.txt` 的内容，确认读取成功
3. 在 `note.txt` 末尾追加内容：「第二次追加」
4. 将最终文件内容写入 `result.txt`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `note_created`: note.txt 是否存在
- `result_created`: result.txt 是否存在
- `has_first_write`: result.txt 是否包含「第一次写入」
- `has_append`: result.txt 是否包含「第二次追加」

## Grading Criteria

- [ ] note_created: note.txt 是否存在
- [ ] result_created: result.txt 是否存在
- [ ] has_first_write: result.txt 是否包含「第一次写入」
- [ ] has_append: result.txt 是否包含「第二次追加」

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    note = workspace_path / "note.txt"
    result = workspace_path / "result.txt"
    if not result.exists():
        return {"note_created":1.0 if note.exists() else 0.0,"result_created":0.0,"has_first_write":0.0,"has_append":0.0}
    c = result.read_text(encoding="utf-8",errors="ignore")
    return {
        "note_created": 1.0 if note.exists() else 0.0,
        "result_created": 1.0,
        "has_first_write": 1.0 if "第一次写入" in c else 0.0,
        "has_append": 1.0 if "第二次追加" in c else 0.0,
    }
```
