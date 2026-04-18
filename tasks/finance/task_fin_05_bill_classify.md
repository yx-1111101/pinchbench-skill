---
id: task_fin_05_bill_classify
name: "账单流水分析 → 收支分类汇总报告"
category: finance
grading_type: automated
timeout_seconds: 450
workspace_files:
  - bills.csv
dataset_dir: dataset/finance/task_fin_05_bill_classify
---

## Prompt

工作区有一份3个月账单流水 `bills.csv`，请读取后生成 `bill_report.md`，必须包含：

1. 三个月总收入 / 总支出 / 净结余
2. 支出按类别分类汇总（餐饮 / 居住 / 交通 / 娱乐 / 订阅 / 其他）
3. 最大支出类别及占比
4. 月度趋势（每月支出对比）
5. 2条节省建议

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden Answers 预计算：总收入 84,000 元 · 总支出 52,340 元 · 最大支出类别：居住）

- `file_created`：bill_report.md 存在
- `total_income_correct`：总收入数字正确（84000±500）
- `total_expense_correct`：总支出数字正确（52340±500）
- `categories_present`：包含至少 5 个支出类别
- `largest_category_correct`：识别出居住是最大支出类别
- `has_suggestions`：包含节省建议相关词

## Grading Criteria

- [ ] （Golden Answers 预计算：总收入 84,000 元 · 总支出 52,340 元 · 最大支出类别：居住）
- [ ] file_created: bill_report.md 存在
- [ ] total_income_correct: 总收入数字正确（84000±500）
- [ ] total_expense_correct: 总支出数字正确（52340±500）
- [ ] categories_present: 包含至少 5 个支出类别
- [ ] largest_category_correct: 识别出居住是最大支出类别
- [ ] has_suggestions: 包含节省建议相关词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "bill_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","total_income_correct","total_expense_correct",
                                   "categories_present","largest_category_correct","has_suggestions"]}
    content = f.read_text(encoding="utf-8")
    # 总收入 84000±500
    income_nums = [int(n.replace(",","")) for n in re.findall(r'[\d,]{4,}', content) if 83500 <= int(n.replace(",","")) <= 84500]
    income_ok = len(income_nums) > 0
    # 总支出 52340±500
    expense_nums = [int(n.replace(",","")) for n in re.findall(r'[\d,]{4,}', content) if 51840 <= int(n.replace(",","")) <= 52840]
    expense_ok = len(expense_nums) > 0
    # 类别
    cats = ["餐饮","居住","交通","娱乐","订阅","其他"]
    cats_found = sum(1 for c in cats if c in content)
    # 最大类别
    largest_ok = "居住" in content and any(w in content for w in ["最大","最高","占比最","第一"])
    has_suggest = any(w in content for w in ["建议","可以","节省","减少","控制"])
    return {
        "file_created":           1.0,
        "total_income_correct":   1.0 if income_ok else 0.0,
        "total_expense_correct":  1.0 if expense_ok else 0.0,
        "categories_present":     1.0 if cats_found >= 5 else 0.0,
        "largest_category_correct":1.0 if largest_ok else 0.0,
        "has_suggestions":        1.0 if has_suggest else 0.0,
    }
```
