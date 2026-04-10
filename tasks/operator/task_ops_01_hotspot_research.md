---
id: task_ops_01_hotspot_research
name: "行业热点聚合 → 选题策划报告"
category: operator
grading_type: hybrid
timeout_seconds: 240
workspace_files: []
dataset_dir: dataset/operator/task_ops_01_hotspot_research
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

你是一名科技数码品牌的内容运营，请联网搜索**今天**科技/数码/消费电子领域的热点事件和趋势话题，生成一份选题策划报告，保存到 `topic_plan.md`。

报告格式要求：
1. **今日热点速览**：列出 5 个值得关注的热点（标题 + 一句话摘要）
2. **选题推荐**：从以上热点中选 2 个，说明为什么适合做内容、适合哪个平台、预估受众
3. **本周内容日历**：基于选题，给出今明后三天各平台的发布建议（一句话即可）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：topic_plan.md 存在
- `file_not_empty`：内容超过 200 字
- `has_five_hotspots`：包含至少 5 个热点（通过编号或标题计数）
- `has_recommendation`：包含"推荐"或平台名称（小红书/抖音/微博/公众号）
- `has_calendar`：包含"今天""明天""后天"或日期

**LLM Judge**：热点时效性与真实性 · 选题逻辑是否充分 · 日历建议是否可落地

## Grading Criteria

- [ ] file_created: topic_plan.md 存在
- [ ] file_not_empty: 内容超过 200 字
- [ ] has_five_hotspots: 包含至少 5 个热点（通过编号或标题计数）
- [ ] has_recommendation: 包含"推荐"或平台名称（小红书/抖音/微博/公众号）
- [ ] has_calendar: 包含"今天""明天""后天"或日期

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "topic_plan.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_five_hotspots","has_recommendation","has_calendar"]}
    content = f.read_text(encoding="utf-8").strip()
    headers = re.findall(r'(?:^#{1,3}\s+.+|^\d+[\.\、].+|^[-\*]\s+\*\*.+)', content, re.MULTILINE)
    has_rec = any(w in content for w in ["推荐","小红书","抖音","微博","公众号","B站","视频号"])
    has_cal = any(w in content for w in ["今天","明天","后天","周一","周二","周三","周四","周五","周六","周日"])
    return {
        "file_created":       1.0,
        "file_not_empty":     1.0 if len(content) > 200 else 0.0,
        "has_five_hotspots":  1.0 if len(headers) >= 5 else 0.0,
        "has_recommendation": 1.0 if has_rec else 0.0,
        "has_calendar":       1.0 if has_cal else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：热点时效性与真实性 · 选题逻辑是否充分 · 日历建议是否可落地

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
