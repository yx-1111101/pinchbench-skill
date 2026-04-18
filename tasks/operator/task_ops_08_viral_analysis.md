---
id: task_ops_08_viral_analysis
name: "爆文归因分析（为什么这篇火了）"
category: operator
grading_type: llm_judge
timeout_seconds: 120
workspace_files:
  - viral_post_data.txt
dataset_dir: dataset/operator/task_ops_08_viral_analysis
---

## Prompt

工作区有一份爆文数据报告 `viral_post_data.txt`，记录了一篇小红书爆文的详细数据（曝光/点赞/收藏/评论/评论关键词等）。

请写一份爆文归因分析报告 `viral_analysis.md`，从以下维度分析为什么这篇内容爆了：

1. **内容层面**：标题/选题/切入角度的亮点
2. **数据信号**：哪个指标最异常？说明什么？
3. **评论区洞察**：评论关键词反映了什么用户需求？
4. **可复制因素**：哪些要素是下次可以复用的？
5. **运气成分**：有哪些是偶然的、不可复制的？

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：viral_analysis.md 存在
- `file_not_empty`：内容超过 300 字
- `covers_five_dimensions`：包含以上 5 个维度的关键词（内容/数据/评论/复制/运气或偶然）
- `mentions_key_metric`：提到收藏率或具体数据指标
- `has_actionable_output`：包含"下次""可以""建议""复用"等可执行词

**LLM Judge**：分析是否有洞见（不是复述数据） · 归因是否合理 · 可复制因素是否具体

## Grading Criteria

- [ ] file_created: viral_analysis.md 存在
- [ ] file_not_empty: 内容超过 300 字
- [ ] covers_five_dimensions: 包含以上 5 个维度的关键词（内容/数据/评论/复制/运气或偶然）
- [ ] mentions_key_metric: 提到收藏率或具体数据指标
- [ ] has_actionable_output: 包含"下次""可以""建议""复用"等可执行词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "viral_analysis.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","covers_five_dimensions",
                                   "mentions_key_metric","has_actionable_output"]}
    content = f.read_text(encoding="utf-8").strip()
    dim_keywords = [
        ["内容","标题","选题","角度"],
        ["数据","指标","收藏","点赞","曝光"],
        ["评论","用户","需求","关键词"],
        ["复制","复用","下次","可以"],
        ["运气","偶然","不可控","随机"],
    ]
    dims_found = sum(1 for kws in dim_keywords if any(w in content for w in kws))
    has_metric  = any(w in content for w in ["收藏率","点赞率","阅读率","12.5%","3.2%","转化"])
    has_action  = any(w in content for w in ["下次","可以","建议","复用","尝试"])
    return {
        "file_created":            1.0,
        "file_not_empty":          1.0 if len(content) > 300 else 0.0,
        "covers_five_dimensions":  1.0 if dims_found >= 4 else 0.0,
        "mentions_key_metric":     1.0 if has_metric else 0.0,
        "has_actionable_output":   1.0 if has_action else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 分析是否有洞见（不是复述数据） · 归因是否合理 · 可复制因素是否具体分析是否有洞见（不是复述数据） · 归因是否合理 · 可复制因素是否具体

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
