---
id: task_ops_12_competitor_monitor
name: "竞品内容监控 + 爆文拆解"
category: operator
grading_type: hybrid
timeout_seconds: 900
workspace_files: []
dataset_dir: dataset/operator/task_ops_12_competitor_monitor
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

请联网调研以下两个竞品品牌在小红书/抖音上**最近一个月**的内容表现：

- **竞品A**：索尼耳机（Sony WF/WH 系列）
- **竞品B**：漫步者耳机（EDIFIER）

生成竞品监控报告 `competitor_report.md`，包含：

1. **各平台近期爆文**：每个品牌找 1-2 篇近期高互动内容，描述其标题/内容形式/互动数据
2. **内容策略对比**：两个品牌的内容风格有何不同？
3. **爆文拆解**：选其中一篇爆文，分析为什么火（参考维度：选题/形式/时机/平台算法）
4. **对我方的启示**：给出 2 条可以借鉴的具体动作

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：competitor_report.md 存在
- `mentions_both_brands`：提到索尼和漫步者（或 Sony / EDIFIER）
- `has_content_comparison`：包含对比相关词（"相比""对比""而""不同""区别"）
- `has_viral_analysis`：包含爆文分析相关词（"爆文""高互动""火""传播"）
- `has_actionable_tips`：包含"可以""借鉴""我们""建议"等行动词

**LLM Judge**：信息时效性 · 爆文拆解是否有洞见 · 启示是否具体可落地

## Grading Criteria

- [ ] file_created: competitor_report.md 存在
- [ ] mentions_both_brands: 提到索尼和漫步者（或 Sony / EDIFIER）
- [ ] has_content_comparison: 包含对比相关词（"相比""对比""而""不同""区别"）
- [ ] has_viral_analysis: 包含爆文分析相关词（"爆文""高互动""火""传播"）
- [ ] has_actionable_tips: 包含"可以""借鉴""我们""建议"等行动词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "competitor_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","mentions_both_brands","has_content_comparison",
                                   "has_viral_analysis","has_actionable_tips"]}
    content = f.read_text(encoding="utf-8")
    has_both = (("索尼" in content or "Sony" in content or "SONY" in content) and
                ("漫步者" in content or "EDIFIER" in content or "Edifier" in content))
    has_compare = any(w in content for w in ["相比","对比","而","不同","区别","差异","VS","vs"])
    has_viral   = any(w in content for w in ["爆文","高互动","火了","传播","热门","爆款"])
    has_action  = any(w in content for w in ["可以","借鉴","我们","建议","参考","学习"])
    return {
        "file_created":          1.0,
        "mentions_both_brands":  1.0 if has_both else 0.0,
        "has_content_comparison":1.0 if has_compare else 0.0,
        "has_viral_analysis":    1.0 if has_viral else 0.0,
        "has_actionable_tips":   1.0 if has_action else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 信息时效性 · 爆文拆解是否有洞见 · 启示是否具体可落地信息时效性 · 爆文拆解是否有洞见 · 启示是否具体可落地

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
