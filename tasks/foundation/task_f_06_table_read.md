---
id: task_f_06_table_read
name: "task_f_06_table_read"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_06_table_read
---

## Prompt

工作区有一个 CSV 文件 `sales.csv`：

请回答：哪个月销售额最高？将答案保存到 `answer.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: answer.txt 是否存在
- `has_answer`: 文件内容是否为非空（不评估正确性/相关性）

## Grading Criteria

- [ ] file_created: answer.txt 是否存在
- [ ] has_answer: 文件内容是否为非空（不评估正确性/相关性）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "answer.txt"
    if not f.exists():
        return {"file_created": 0.0, "has_answer": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()

    return {
        "file_created": 1.0,
        "has_answer": 1.0 if len(content) > 0 else 0.0,
    }
```
