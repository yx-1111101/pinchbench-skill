---
id: task_fin_03_financial_extract
name: "财报表格 → 关键指标结构化提取"
category: finance
grading_type: automated
timeout_seconds: 540
workspace_files:
  - financial_data.xlsx
dataset_dir: dataset/finance/task_fin_03_financial_extract
---

## Prompt

工作区有一份公司财报数据表格 `financial_data.xlsx`，请提取关键指标，生成报告 `financial_report.md`，必须包含：

- 总营收（total_revenue）
- 总利润（total_profit）
- 利润最高的业务线（top_product）
- 营收最高的地区（top_region）
- 总费用（total_expenses）
- 与预算的对比情况（budget_comparison）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `report_created`：financial_report.md 存在
- `total_revenue`：报告中包含正确的总营收数值
- `total_profit`：报告中包含正确的总利润数值
- `top_region`：正确识别营收最高地区
- `top_product`：正确识别利润最高业务线
- `total_expenses`：报告中包含总费用数值
- `budget_comparison`：包含预算对比相关描述

## Grading Criteria

- [ ] report_created: financial_report.md 存在
- [ ] total_revenue: 报告中包含正确的总营收数值
- [ ] total_profit: 报告中包含正确的总利润数值
- [ ] top_region: 正确识别营收最高地区
- [ ] top_product: 正确识别利润最高业务线
- [ ] total_expenses: 报告中包含总费用数值
- [ ] budget_comparison: 包含预算对比相关描述

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    # 注意：正确数值从 GOLDEN 变量获取，此处为结构示意
    # 实际运行时 benchmark 会注入 GOLDEN dict
    GOLDEN = {
        "total_revenue": "2450",   # 从 dataset 文件计算得出
        "total_profit":  "380",
        "top_region":    "华东",
        "top_product":   "企业服务",
        "total_expenses":"2070",
    }
    f = workspace_path / "financial_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["report_created","total_revenue","total_profit",
                                   "top_region","top_product","total_expenses","budget_comparison"]}
    content = f.read_text(encoding="utf-8")
    return {
        "report_created":   1.0,
        "total_revenue":    1.0 if GOLDEN["total_revenue"] in content else 0.0,
        "total_profit":     1.0 if GOLDEN["total_profit"] in content else 0.0,
        "top_region":       1.0 if GOLDEN["top_region"] in content else 0.0,
        "top_product":      1.0 if GOLDEN["top_product"] in content else 0.0,
        "total_expenses":   1.0 if GOLDEN["total_expenses"] in content else 0.0,
        "budget_comparison":1.0 if any(w in content for w in ["预算","budget","对比","超出","低于"]) else 0.0,
    }
```
