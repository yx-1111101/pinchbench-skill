---
id: task_ops_11_growth_strategy
name: "粉丝增长策略建议（基于账号诊断数据）"
category: operator
grading_type: llm_judge
timeout_seconds: 360
workspace_files:
  - account_data.txt
dataset_dir: dataset/operator/task_ops_11_growth_strategy
---

## Prompt

工作区有一份账号诊断数据报告 `account_data.txt`，记录了某科技品牌小红书账号 6 个月的运营数据和当前问题。

请基于数据，生成一份 **未来 3 个月的粉丝增长策略方案** `growth_plan.md`，包含：

1. **问题诊断**：基于数据，指出最核心的 2-3 个问题
2. **增长目标**：给出合理的 3 个月目标（粉丝数/互动率）
3. **内容策略**：具体的内容方向调整（不要说"做好内容"这种废话）
4. **执行计划**：每月重点动作（3 个月分别做什么）
5. **KOL 合作建议**：如何调整 KOL 合作策略

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：growth_plan.md 存在
- `file_not_empty`：内容超过 400 字
- `addresses_known_issues`：提到了 dataset 中明确指出的问题（视频/广告占比/互动）
- `has_numeric_goal`：包含具体数字目标（粉丝数或百分比）
- `has_monthly_plan`：包含月度计划（"第一个月""第二个月"或"1月""2月"）

**LLM Judge**：诊断是否准确切中数据中的问题 · 策略是否具体可执行 · 目标是否合理

## Grading Criteria

- [ ] file_created: growth_plan.md 存在
- [ ] file_not_empty: 内容超过 400 字
- [ ] addresses_known_issues: 提到了 dataset 中明确指出的问题（视频/广告占比/互动）
- [ ] has_numeric_goal: 包含具体数字目标（粉丝数或百分比）
- [ ] has_monthly_plan: 包含月度计划（"第一个月""第二个月"或"1月""2月"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "growth_plan.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","addresses_known_issues",
                                   "has_numeric_goal","has_monthly_plan"]}
    content = f.read_text(encoding="utf-8").strip()
    issue_kws = ["视频","广告","互动","回复率","促销","IP","栏目","中腰部"]
    issues_found = sum(1 for w in issue_kws if w in content)
    has_goal  = bool(re.search(r'\d+[\.,]?\d*\s*[万个%％]', content))
    has_month = any(w in content for w in ["第一个月","第二个月","第三个月","月一","月二","月三","Month 1"])
    return {
        "file_created":           1.0,
        "file_not_empty":         1.0 if len(content) > 400 else 0.0,
        "addresses_known_issues": 1.0 if issues_found >= 3 else 0.0,
        "has_numeric_goal":       1.0 if has_goal else 0.0,
        "has_monthly_plan":       1.0 if has_month else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 诊断是否准确切中数据中的问题 · 策略是否具体可执行 · 目标是否合理诊断是否准确切中数据中的问题 · 策略是否具体可执行 · 目标是否合理

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
