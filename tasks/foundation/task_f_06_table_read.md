---
id: task_f_06_table_read
name: "task_f_06_table_read"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files:
  - sales.csv
dataset_dir: dataset/foundation/task_f_06_table_read
---

## Prompt

工作区有一个 CSV 文件 `sales.csv`：

请回答：哪个月销售额最高？将答案保存到 `answer.txt`。

## Expected Behavior

The agent should read `sales.csv`, determine which month has the highest sales amount, and write that answer to `answer.txt`. The grader recomputes the correct month from the same CSV and checks that the answer matches (supports 2月 / February / 91000 等合理表述).

Evaluation criteria:
- `file_created`: answer.txt 是否存在
- `answer_correct`: 答案是否与由 `sales.csv` 计算出的金标一致

## Grading Criteria

- [ ] file_created: answer.txt 是否存在
- [ ] answer_correct: 是否答对「销售额最高的月份」

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    import csv

    workspace_path = Path(workspace_path)
    ans_path = workspace_path / "answer.txt"
    csv_path = workspace_path / "sales.csv"

    if not ans_path.exists():
        return {"file_created": 0.0, "answer_correct": 0.0}

    raw = ans_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not csv_path.exists():
        return {"file_created": 1.0, "answer_correct": 0.0}

    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig", errors="ignore") as fp:
        for row in csv.DictReader(fp):
            rows.append(row)

    best_month = None
    best_val = None
    for row in rows:
        m = (row.get("月份") or "").strip()
        amt_s = (row.get("销售额") or "").replace(",", "").strip()
        try:
            amt = int(amt_s)
        except ValueError:
            continue
        if best_val is None or amt > best_val:
            best_val = amt
            best_month = m

    if best_val is None:
        return {"file_created": 1.0, "answer_correct": 0.0}

    nums = raw.replace(",", "").replace("，", "")
    amount_ok = str(best_val) in nums
    month_ok = bool(best_month and best_month in raw)
    rl = raw.lower()
    if best_month and "2" in best_month:
        month_ok = month_ok or ("二月" in raw) or ("feb" in rl)

    ok = amount_ok or month_ok

    return {
        "file_created": 1.0,
        "answer_correct": 1.0 if ok else 0.0,
    }
```
