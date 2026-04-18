---
id: task_ops_13_crisis_pr
name: "负面舆情发现与摘要 + 危机公关话术生成"
category: operator
grading_type: hybrid
timeout_seconds: 720
workspace_files: []
dataset_dir: dataset/operator/task_ops_13_crisis_pr
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

品牌名称：极光科技 / AuraPods Pro 耳机

请完成两个任务：

**任务一：舆情巡查**
联网搜索该品牌/产品近期（最近30天）的负面评价或投诉内容，生成舆情摘要。
- 如搜索未发现明显负面内容，用「低风险」结论说明，并列出搜索路径

**任务二：危机话术模板**
针对以下两个真实投诉场景（来自 ops_09 的 MSG_004），生成完整的危机公关话术：

场景A：用户公开发帖投诉「购买一个月后左耳没声音，售后要等15个工作日」
- 需要：官方公开回复话术（发布在评论区）

场景B：假设此事被科技媒体报道，标题为「国产耳机极光科技：售后响应慢，消费者维权难」
- 需要：品牌声明草稿（对外发布）

将所有内容保存到 `crisis_report.md`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：crisis_report.md 存在
- `file_not_empty`：内容超过 300 字
- `has_sentiment_scan`：包含舆情巡查结果（"未发现""低风险""负面"等词）
- `has_public_reply`：包含场景A的公开回复话术（包含"感谢""抱歉"或"您好"）
- `has_press_statement`：包含场景B的声明草稿（包含"声明""致""用户"）

**LLM Judge**：舆情判断是否合理 · 危机话术是否专业得体 · 品牌声明是否有诚意且不推卸责任

## Grading Criteria

- [ ] file_created: crisis_report.md 存在
- [ ] file_not_empty: 内容超过 300 字
- [ ] has_sentiment_scan: 包含舆情巡查结果（"未发现""低风险""负面"等词）
- [ ] has_public_reply: 包含场景A的公开回复话术（包含"感谢""抱歉"或"您好"）
- [ ] has_press_statement: 包含场景B的声明草稿（包含"声明""致""用户"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "crisis_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_sentiment_scan",
                                   "has_public_reply","has_press_statement"]}
    content = f.read_text(encoding="utf-8").strip()
    has_scan     = any(w in content for w in ["未发现","低风险","负面","舆情","风险","投诉"])
    has_reply    = any(w in content for w in ["您好","感谢","抱歉","非常抱歉","亲爱的"])
    has_stmt     = any(w in content for w in ["声明","致广大用户","郑重","承诺","说明"])
    return {
        "file_created":        1.0,
        "file_not_empty":      1.0 if len(content) > 300 else 0.0,
        "has_sentiment_scan":  1.0 if has_scan else 0.0,
        "has_public_reply":    1.0 if has_reply else 0.0,
        "has_press_statement": 1.0 if has_stmt else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 舆情判断是否合理 · 危机话术是否专业得体 · 品牌声明是否有诚意且不推卸责任舆情判断是否合理 · 危机话术是否专业得体 · 品牌声明是否有诚意且不推卸责任

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
