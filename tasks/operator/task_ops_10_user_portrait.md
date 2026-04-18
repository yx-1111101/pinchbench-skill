---
id: task_ops_10_user_portrait
name: "用户画像提炼（从评论中总结谁在看、谁在买）"
category: operator
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - comments.txt
dataset_dir: dataset/operator/task_ops_10_user_portrait
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

工作区有一份小红书评论抽样数据 `comments.txt`（100 条真实用户评论）。

请分析评论，生成一份用户画像报告 `user_portrait.md`，包含：

1. **核心用户群体**：2-3 个典型用户画像（给每个起个名字，如"通勤白领小张"）
2. **购买动机分布**：主要购买原因排序（工作需求/礼物/学习/运动/其他）
3. **使用场景 TOP5**：最常提到的使用场景
4. **内容偏好信号**：他们对什么内容话题最感兴趣（从评论推断）
5. **运营建议**：基于画像，给出 2 条内容方向建议

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：user_portrait.md 存在
- `file_not_empty`：内容超过 400 字
- `has_persona`：包含用户画像描述（识别职业/年龄/场景词）
- `has_scenarios`：包含场景相关词（"通勤""健身""工作""学习""咖啡馆"）
- `has_suggestions`：包含建议相关词

**LLM Judge**：画像是否有洞见（不是罗列数据） · 用户群是否清晰区分 · 建议是否能直接指导内容策划

## Grading Criteria

- [ ] file_created: user_portrait.md 存在
- [ ] file_not_empty: 内容超过 400 字
- [ ] has_persona: 包含用户画像描述（识别职业/年龄/场景词）
- [ ] has_scenarios: 包含场景相关词（"通勤""健身""工作""学习""咖啡馆"）
- [ ] has_suggestions: 包含建议相关词

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "user_portrait.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_persona","has_scenarios","has_suggestions"]}
    content = f.read_text(encoding="utf-8").strip()
    persona_kws  = ["职场","学生","白领","程序员","设计师","运营","宝妈","25","28","30"]
    scenario_kws = ["通勤","健身","工作","学习","咖啡馆","地铁","运动","办公","图书馆"]
    suggest_kws  = ["建议","可以","应该","方向","策略","尝试"]
    return {
        "file_created":   1.0,
        "file_not_empty": 1.0 if len(content) > 400 else 0.0,
        "has_persona":    1.0 if any(w in content for w in persona_kws) else 0.0,
        "has_scenarios":  1.0 if sum(1 for w in scenario_kws if w in content) >= 3 else 0.0,
        "has_suggestions":1.0 if any(w in content for w in suggest_kws) else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 画像是否有洞见（不是罗列数据） · 用户群是否清晰区分 · 建议是否能直接指导内容策划画像是否有洞见（不是罗列数据） · 用户群是否清晰区分 · 建议是否能直接指导内容策划

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
