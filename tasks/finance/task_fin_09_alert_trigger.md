---
id: task_fin_09_alert_trigger
name: "规则触发告警判断 → 生成通知报告"
category: finance
grading_type: automated
timeout_seconds: 90
workspace_files:
  - prices_today.json
  - watchlist.json
dataset_dir: dataset/finance/task_fin_09_alert_trigger
---

## Prompt

工作区有持仓告警规则文件 `watchlist.json` 和今日价格数据 `prices_today.json`，请判断哪些告警规则被触发，生成通知报告 `alert_report.md`，包含：

- 触发的告警列表（标明股票+触发原因）
- 各持仓当前盈亏状态
- 未触发规则的当前距离阈值

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden Answers：应触发2条告警 — **茅台跌破成本价区域** + **英伟达盈利超50%建议减仓**；腾讯无告警）

- `file_created`：alert_report.md 存在
- `maotai_alert_triggered`：包含茅台告警（「茅台」+「跌破」或「1700」）
- `nvda_alert_triggered`：包含英伟达止盈告警（「英伟达」+「止盈」或「50%」或「减仓」）
- `tencent_no_alert`：报告提到腾讯，且明确说明腾讯当前未触发告警
- `alert_count_correct`：只有2条告警（不多不少）
- `has_distance_info`：包含距离阈值描述（「距」或「还差」或「差」）

## Grading Criteria

- [ ] （Golden Answers：应触发2条告警 — **茅台跌破成本价区域** + **英伟达盈利超50%建议减仓**；腾讯无告警）
- [ ] file_created: alert_report.md 存在
- [ ] maotai_alert_triggered: 包含茅台告警（「茅台」+「跌破」或「1700」）
- [ ] nvda_alert_triggered: 包含英伟达止盈告警（「英伟达」+「止盈」或「50%」或「减仓」）
- [ ] tencent_no_alert: 报告提到腾讯，且明确说明腾讯当前未触发告警
- [ ] alert_count_correct: 只有2条告警（不多不少）
- [ ] has_distance_info: 包含距离阈值描述（「距」或「还差」或「差」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "alert_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","maotai_alert_triggered","nvda_alert_triggered",
                                   "tencent_no_alert","alert_count_correct","has_distance_info"]}
    content = f.read_text(encoding="utf-8")
    maotai_ok  = "茅台" in content and any(w in content for w in ["跌破","1700","成本价"])
    nvda_ok    = "英伟达" in content and any(w in content for w in ["止盈","50%","50％","减仓"])
    tencent_section = re.search(r'腾讯.{0,180}', content, re.DOTALL)
    tencent_safe = bool(tencent_section) and any(
        w in tencent_section.group(0) for w in ["未触发","无告警","未达到阈值","未满足条件"]
    ) and not any(
        w in tencent_section.group(0) for w in ["⚠","警报"]
    )
    alert_lines = [line for line in content.splitlines() if any(w in line for w in ["⚠","触发","告警","警报","alert"])]
    count_ok = len(alert_lines) == 2 and maotai_ok and nvda_ok and tencent_safe
    has_dist = any(w in content for w in ["距","还差","差","距离","away"])
    return {
        "file_created":         1.0,
        "maotai_alert_triggered":1.0 if maotai_ok else 0.0,
        "nvda_alert_triggered": 1.0 if nvda_ok else 0.0,
        "tencent_no_alert":     1.0 if tencent_safe else 0.0,
        "alert_count_correct":  1.0 if count_ok else 0.0,
        "has_distance_info":    1.0 if has_dist else 0.0,
    }
```
