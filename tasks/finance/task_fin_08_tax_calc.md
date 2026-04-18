---
id: task_fin_08_tax_calc
name: "年度个税汇算清缴计算"
category: finance
grading_type: automated
timeout_seconds: 150
workspace_files:
  - tax_info.txt
dataset_dir: dataset/finance/task_fin_08_tax_calc
---

## Prompt

工作区有纳税人信息文件 `tax_info.txt`，请计算2025年度个税汇算清缴，生成 `tax_report.md`，必须包含：

- 综合所得计算过程
- 应纳税所得额
- 适用税率
- 应纳税额
- 已预缴税款
- 应补 / 退税金额

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden Answers：综合所得 356,200 元 · 应纳税所得额 199,480 元 · 应纳税额 22,976 元 · **应退税 13,928 元**）

- `file_created`：tax_report.md 存在
- `comprehensive_income_correct`：综合所得额正确（356200±100）
- `taxable_income_correct`：应纳税所得额正确（199480±200）
- `tax_payable_correct`：应纳税额正确（22976±100）
- `refund_correct`：退税金额正确（13928±200）
- `shows_calculation`：包含计算过程（含「-」或「×」或「=」）

## Grading Criteria

- [ ] （Golden Answers：综合所得 356,200 元 · 应纳税所得额 199,480 元 · 应纳税额 22,976 元 · **应退税 13,928 元**）
- [ ] file_created: tax_report.md 存在
- [ ] comprehensive_income_correct: 综合所得额正确（356200±100）
- [ ] taxable_income_correct: 应纳税所得额正确（199480±200）
- [ ] tax_payable_correct: 应纳税额正确（22976±100）
- [ ] refund_correct: 退税金额正确（13928±200）
- [ ] shows_calculation: 包含计算过程（含「-」或「×」或「=」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "tax_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","comprehensive_income_correct","taxable_income_correct",
                                   "tax_payable_correct","refund_correct","shows_calculation"]}
    content = f.read_text(encoding="utf-8")
    all_nums = [int(n.replace(",","")) for n in re.findall(r'[\d,]{4,}', content)]
    income_ok  = any(356100 <= n <= 356300 for n in all_nums)
    taxable_ok = any(199280 <= n <= 199680 for n in all_nums)
    payable_ok = any(22876 <= n <= 23076 for n in all_nums)
    refund_ok  = any(13728 <= n <= 14128 for n in all_nums)
    calc_ok    = bool(re.search(r'[-−×÷=]', content))
    return {
        "file_created":                 1.0,
        "comprehensive_income_correct": 1.0 if income_ok else 0.0,
        "taxable_income_correct":       1.0 if taxable_ok else 0.0,
        "tax_payable_correct":          1.0 if payable_ok else 0.0,
        "refund_correct":               1.0 if refund_ok else 0.0,
        "shows_calculation":            1.0 if calc_ok else 0.0,
    }
```
