---
id: task_f_05_pdf_parse
name: "task_f_05_pdf_parse"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_05_pdf_parse
---

## Prompt

工作区有一个 PDF 文件 `report.pdf`，内容是一份产品报告。

请提取 PDF 全文，保存为 `extracted.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: extracted.txt 是否存在
- `has_content`: 内容是否为非空（不评估正确性/相关性）

## Grading Criteria

- [ ] file_created: extracted.txt 是否存在
- [ ] has_content: 内容是否为非空（不评估正确性/相关性）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "extracted.txt"
    if not f.exists():
        return {"file_created": 0.0, "has_content": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()

    return {
        "file_created": 1.0,
        "has_content": 1.0 if len(content) > 0 else 0.0,
    }
```
