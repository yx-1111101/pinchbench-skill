---
id: task_f_12_long_context
name: "task_f_12_long_context"
category: foundation
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/foundation/task_f_12_long_context
---

## Prompt

工作区有一份长文档 `long_doc.txt`。文中恰好有一处「隐藏关键词：」开头的短句，请阅读全文，找到该句，把**冒号后面的关键词语**写入 `answer.txt`。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：`answer.txt` 是否存在  
- `has_answer`：文件内容去空白后长度 ≥ 1  
- `keyword_correct`：答案中含金标短语（由 `long_doc.txt` 解析）

## Grading Criteria

- [ ] file_created: `answer.txt` 是否存在
- [ ] has_answer: 文件内容去空白后长度 ≥ 1
- [ ] keyword_correct: 答案中含金标短语（由 `long_doc.txt` 解析）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re

    def extract_golden(doc_text):
        m = re.search(r"隐藏关键词[：:]\s*([^。\n\r]+?)(?:\s*。|\s*$)", doc_text)
        if not m:
            m = re.search(r"隐藏关键词[：:]\s*([^\n\r]+)", doc_text)
        return (m.group(1).strip() if m else None)

    ans = workspace_path / "answer.txt"
    doc = workspace_path / "long_doc.txt"

    if not ans.exists():
        return {"file_created": 0.0, "has_answer": 0.0, "keyword_correct": 0.0}

    raw = ans.read_text(encoding="utf-8", errors="ignore").strip()
    golden = None
    if doc.exists():
        golden = extract_golden(doc.read_text(encoding="utf-8", errors="ignore"))

    ok_kw = bool(golden) and golden in raw

    return {
        "file_created": 1.0,
        "has_answer": 1.0 if len(raw) > 0 else 0.0,
        "keyword_correct": 1.0 if ok_kw else 0.0,
    }
```
