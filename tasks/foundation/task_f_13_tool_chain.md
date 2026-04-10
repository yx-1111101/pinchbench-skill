---
id: task_f_13_tool_chain
name: "task_f_13_tool_chain"
category: foundation
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/foundation/task_f_13_tool_chain
---

## Prompt

请完成以下需要多工具串联的任务：

1. 搜索「特斯拉 Model 3 2026款价格」
2. 读取工作区文件 `budget.txt`
3. 根据搜索结果和预算，判断是否负担得起
4. 将判断结果和依据写入 `conclusion.txt`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `conclusion_created`: conclusion.txt 是否存在
- `has_content`: conclusion.txt 内容是否为非空（不评估正确性/合理性）

## Grading Criteria

- [ ] conclusion_created: conclusion.txt 是否存在
- [ ] has_content: conclusion.txt 内容是否为非空（不评估正确性/合理性）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "conclusion.txt"
    if not f.exists():
        return {
            "conclusion_created": 0.0,
            "has_content": 0.0,
        }

    content = f.read_text(encoding="utf-8", errors="ignore").strip()

    return {
        "conclusion_created": 1.0,
        "has_content": 1.0 if len(content) > 0 else 0.0,
    }
```
