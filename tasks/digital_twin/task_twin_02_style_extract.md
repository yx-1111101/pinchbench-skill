---
id: task_twin_02_style_extract
name: "冷启动 — 历史文章样本 → 提炼写作风格规则"
category: digital_twin
grading_type: llm_judge
timeout_seconds: 150
workspace_files: []
dataset_dir: dataset/digital_twin/task_twin_02_style_extract
---

## Prompt

工作区有陈默写过的3篇文章样本 `article_01.txt`、`article_02.txt`、`article_03.txt`。

请分析后生成写作风格指南 `style_guide.md`，包含：

1. **句式习惯**：常用句型、句子长短偏好
2. **词汇偏好**：高频词、标志性用语、刻意回避的词
3. **结构模式**：文章的起承转合规律
4. **语气标定**：在严肃↔轻松、理性↔感性轴上的位置
5. **可操作的写作规则**：5条「写陈默风格时必须遵守的规则」

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：style_guide.md 存在
- `file_not_empty`：内容超过 300 字
- `has_five_rules`：包含至少5条编号规则
- `has_tone_analysis`：包含语气分析词（严肃/轻松/理性/感性至少2个）

**LLM Judge**：规则是否具体可操作 · 是否真从样本提炼而非泛泛而谈

## Grading Criteria

- [ ] file_created: style_guide.md 存在
- [ ] file_not_empty: 内容超过 300 字
- [ ] has_five_rules: 包含至少5条编号规则
- [ ] has_tone_analysis: 包含语气分析词（严肃/轻松/理性/感性至少2个）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "style_guide.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_five_rules","has_tone_analysis"]}
    content = f.read_text(encoding="utf-8").strip()
    rules = re.findall(r'(?:^[1-5][.、]|^[①-⑤]).+', content, re.MULTILINE)
    tone_words = ["严肃","轻松","理性","感性","权威","平等","直接","口语"]
    has_tone = sum(1 for w in tone_words if w in content) >= 2
    return {
        "file_created":      1.0,
        "file_not_empty":    1.0 if len(content) > 300 else 0.0,
        "has_five_rules":    1.0 if len(rules) >= 5 else 0.0,
        "has_tone_analysis": 1.0 if has_tone else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：规则是否具体可操作 · 是否真从样本提炼而非泛泛而谈

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
