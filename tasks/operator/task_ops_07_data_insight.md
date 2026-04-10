---
id: task_ops_07_data_insight
name: "运营数据解读 → 找异动 + 归因分析"
category: operator
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/operator/task_ops_07_data_insight
---

## Prompt

工作区有一份运营周报数据表 `weekly_stats.csv`，记录了某科技品牌在微信公众号、小红书、抖音三个平台连续 6 周（2025W01-W06）的内容数据。

请分析数据，将结论保存到 `insight_report.md`，必须回答：

1. **哪个平台、哪一周出现了最显著的正向异动？**（具体数字支撑）
2. **哪个平台在后期出现了质量下滑信号？**（用取关数或阅读量说明）
3. **抖音的整体表现如何？**（一句话结论）
4. **给运营团队的 2 条具体建议**

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（Golden answers 基于 dataset 预计算）

- `file_created`：insight_report.md 存在
- `identified_xiaohongshu_w04`：提到小红书 W04 的正向异动（包含"小红书"和"W04"或"第4周"）
- `identified_churn_signal`：提到取关数上升或粉丝质量下降（包含"取关"或"流失"）
- `douyin_stable`：提到抖音表现平稳（包含"抖音"和"平稳"或"稳定"）
- `has_data_evidence`：报告中包含具体数字（至少 3 个数字）
- `has_suggestions`：包含建议相关词（"建议""应该""可以""推荐"）

## Grading Criteria

- [ ] （Golden answers 基于 dataset 预计算）
- [ ] file_created: insight_report.md 存在
- [ ] identified_xiaohongshu_w04: 提到小红书 W04 的正向异动（包含"小红书"和"W04"或"第4周"）
- [ ] identified_churn_signal: 提到取关数上升或粉丝质量下降（包含"取关"或"流失"）
- [ ] douyin_stable: 提到抖音表现平稳（包含"抖音"和"平稳"或"稳定"）
- [ ] has_data_evidence: 报告中包含具体数字（至少 3 个数字）
- [ ] has_suggestions: 包含建议相关词（"建议""应该""可以""推荐"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "insight_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","identified_xiaohongshu_w04",
                                   "identified_churn_signal","douyin_stable",
                                   "has_data_evidence","has_suggestions"]}
    content = f.read_text(encoding="utf-8")
    has_xhs_w04  = "小红书" in content and bool(re.search(r'W04|第4周|第四周', content))
    has_churn    = any(w in content for w in ["取关","流失","掉粉","取消关注"])
    has_douyin   = "抖音" in content and any(w in content for w in ["平稳","稳定","波动不大","变化不大"])
    numbers      = re.findall(r'\d+[\.,]?\d*\s*[%％万千]?', content)
    has_data     = len(numbers) >= 3
    has_suggest  = any(w in content for w in ["建议","应该","可以尝试","推荐","需要"])
    return {
        "file_created":               1.0,
        "identified_xiaohongshu_w04": 1.0 if has_xhs_w04 else 0.0,
        "identified_churn_signal":    1.0 if has_churn else 0.0,
        "douyin_stable":              1.0 if has_douyin else 0.0,
        "has_data_evidence":          1.0 if has_data else 0.0,
        "has_suggestions":            1.0 if has_suggest else 0.0,
    }
```
