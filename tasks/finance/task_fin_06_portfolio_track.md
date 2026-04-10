---
id: task_fin_06_portfolio_track
name: "投资组合追踪 → 持仓分析 + 盈亏计算"
category: finance
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/finance/task_fin_06_portfolio_track
---

## Prompt

工作区有持仓记录 `portfolio.csv` 和今日价格数据 `prices_today.json`，请生成持仓分析报告 `portfolio_report.md`，包含：

1. 各持仓当前市值、盈亏金额、盈亏比例
2. 组合总市值、总盈亏
3. 盈利 / 亏损最大的持仓
4. 各持仓占比

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden Answers：总盈亏 +26,650 元 · 英伟达盈利最多 +8,850 元 · 腾讯亏损最多 -7,000 元）

- `file_created`：portfolio_report.md 存在
- `total_profit_correct`：总盈亏在正确范围（+26650±1000，港股汇率有浮动）
- `nvda_profit_correct`：英伟达盈亏正确（+8850±500）
- `tencent_loss_correct`：腾讯亏损识别正确（报告中腾讯对应负数）
- `has_percentage`：包含盈亏百分比
- `has_all_positions`：五支持仓都有提到

## Grading Criteria

- [ ] （Golden Answers：总盈亏 +26,650 元 · 英伟达盈利最多 +8,850 元 · 腾讯亏损最多 -7,000 元）
- [ ] file_created: portfolio_report.md 存在
- [ ] total_profit_correct: 总盈亏在正确范围（+26650±1000，港股汇率有浮动）
- [ ] nvda_profit_correct: 英伟达盈亏正确（+8850±500）
- [ ] tencent_loss_correct: 腾讯亏损识别正确（报告中腾讯对应负数）
- [ ] has_percentage: 包含盈亏百分比
- [ ] has_all_positions: 五支持仓都有提到

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "portfolio_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","total_profit_correct","nvda_profit_correct",
                                   "tencent_loss_correct","has_percentage","has_all_positions"]}
    content = f.read_text(encoding="utf-8")
    # 总盈亏 26650±1000
    all_nums = [int(n.replace(",","")) for n in re.findall(r'[\d,]{4,}', content)]
    total_ok = any(25650 <= n <= 27650 for n in all_nums)
    # 英伟达盈亏 8850±500
    nvda_ok = any(8350 <= n <= 9350 for n in all_nums)
    # 腾讯亏损（找腾讯段落含负号）
    tencent_section = re.search(r'腾讯.{0,200}', content, re.DOTALL)
    tencent_loss = tencent_section and bool(re.search(r'[-−][\d,]+|亏损|负', tencent_section.group(0)))
    has_pct = bool(re.search(r'\d+\.?\d*\s*[%％]', content))
    positions = ["贵州茅台","腾讯","英伟达","苹果","沪深300"]
    all_pos = sum(1 for p in positions if p in content) >= 5
    return {
        "file_created":        1.0,
        "total_profit_correct":1.0 if total_ok else 0.0,
        "nvda_profit_correct": 1.0 if nvda_ok else 0.0,
        "tencent_loss_correct":1.0 if tencent_loss else 0.0,
        "has_percentage":      1.0 if has_pct else 0.0,
        "has_all_positions":   1.0 if all_pos else 0.0,
    }
```
