---
id: task_fin_07_budget_plan
name: "财务规划 → 预算制定 + 执行追踪报告"
category: finance
grading_type: hybrid
timeout_seconds: 540
workspace_files:
  - company_financials.csv
dataset_dir: dataset/finance/task_fin_07_budget_plan
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有某初创公司过去6个月收支数据 `company_financials.csv`，请生成财务规划报告 `budget_plan.md`，包含：

1. 过去6个月收支趋势分析（哪个月最好 / 最差）
2. 各成本项占比及趋势
3. 识别异常：市场费用波动大，说明风险
4. Q2预算建议
5. 给老板的2条控制成本的具体建议

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：budget_plan.md 存在
- `identifies_best_month`：识别出11月净利润最高
- `identifies_worst_month`：识别出12月净利润最低
- `flags_marketing_volatility`：提到市场费用波动（「市场」+「波动」/「增加」/「风险」）
- `has_q2_forecast`：包含未来预测（「Q2」/「预算」/「建议」）

**LLM Judge**：分析是否有洞见 · 预算建议是否合理且具体 · 成本控制建议是否可落地

## Grading Criteria

- [ ] file_created: budget_plan.md 存在
- [ ] identifies_best_month: 识别出11月净利润最高
- [ ] identifies_worst_month: 识别出12月净利润最低
- [ ] flags_marketing_volatility: 提到市场费用波动（「市场」+「波动」/「增加」/「风险」）
- [ ] has_q2_forecast: 包含未来预测（「Q2」/「预算」/「建议」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "budget_plan.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","identifies_best_month","identifies_worst_month",
                                   "flags_marketing_volatility","has_q2_forecast"]}
    content = f.read_text(encoding="utf-8")
    best_ok  = any(w in content for w in ["11月","十一月","2025-11","57000"])
    worst_ok = any(w in content for w in ["12月","十二月","2025-12","20000"])
    mkt_ok   = "市场" in content and any(w in content for w in ["波动","增加","风险","不稳","异常"])
    q2_ok    = any(w in content for w in ["Q2","q2","二季度","预算","下季度"])
    return {
        "file_created":             1.0,
        "identifies_best_month":    1.0 if best_ok else 0.0,
        "identifies_worst_month":   1.0 if worst_ok else 0.0,
        "flags_marketing_volatility":1.0 if mkt_ok else 0.0,
        "has_q2_forecast":          1.0 if q2_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 分析是否有洞见 · 预算建议是否合理且具体 · 成本控制建议是否可落地

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
