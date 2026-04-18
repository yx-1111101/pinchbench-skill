---
id: task_fin_04_daily_brief
name: "多源信息综合 → 每日金融简报"
category: finance
grading_type: hybrid
timeout_seconds: 720
workspace_files: []
dataset_dir: dataset/finance/task_fin_04_daily_brief
grading_weights:
  automated: 0.3
  llm_judge: 0.7
---

## Prompt

请联网收集今日金融市场信息，生成一份 `daily_brief.md`，包含：

- 今日 A股/港股/美股 市场整体表现（指数涨跌）
- 2-3 条今日重要财经新闻摘要
- 今日值得关注的板块或个股异动
- 一句话市场情绪判断

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：daily_brief.md 存在
- `file_not_empty`：内容非空
- `mentions_index`：包含指数名称（「上证」「恒生」「纳斯达克」「道琼斯」「沪深」）
- `has_news`：包含新闻/事件描述（超过 100 字）

**LLM Judge**：信息时效性 · 覆盖完整度 · 分析是否有洞见

## Grading Criteria

- [ ] file_created: daily_brief.md 存在
- [ ] file_not_empty: 内容非空
- [ ] mentions_index: 包含指数名称（「上证」「恒生」「纳斯达克」「道琼斯」「沪深」）
- [ ] has_news: 包含新闻/事件描述（超过 100 字）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "daily_brief.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","mentions_index","has_news"]}
    content = f.read_text(encoding="utf-8").strip()
    mentions_idx = any(w in content for w in ["上证","恒生","纳斯达克","道琼斯","沪深","标普","S&P"])
    has_news = len(content) > 100
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 0 else 0.0,
        "mentions_index": 1.0 if mentions_idx else 0.0,
        "has_news":       1.0 if has_news else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 信息时效性 · 覆盖完整度 · 分析是否有洞见信息时效性 · 覆盖完整度 · 分析是否有洞见

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
