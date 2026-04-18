---
id: task_ops_09_community_reply
name: "社群消息意图识别 + 分类回复"
category: operator
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - messages.txt
dataset_dir: dataset/operator/task_ops_09_community_reply
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有一份社群消息记录 `messages.txt`，包含 10 条来自不同渠道的用户消息（评论/私信）。

请完成两件事，保存到 `reply_sheet.md`：

**第一步：意图分类**
对每条消息标注意图类型：咨询（产品问题）/ 投诉 / 好评 / 砍价 / 媒体合作 / 闲聊

**第二步：生成回复草稿**
对每条消息生成品牌回复，要求：
- 符合品牌调性（专业、亲切、不官方腔）
- 投诉类：道歉 + 给出实际解决方案
- 咨询类：直接回答问题
- 好评类：感谢 + 引导晒单/继续互动
- 媒体合作类：给出转接方式

格式：
```
MSG_001 | 意图：咨询 | 回复：...
MSG_002 | 意图：投诉 | 回复：...
```

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：reply_sheet.md 存在
- `has_ten_replies`：包含 10 条回复（通过 MSG_00x 计数）
- `has_intent_labels`：包含"意图："标注
- `complaint_addressed`：MSG_004（投诉）的回复包含道歉词（"抱歉""对不起""非常遗憾"）
- `media_redirected`：MSG_008（媒体合作）的回复包含联系方式引导词（"联系""邮件""转接"）

**LLM Judge**：意图识别准确率 · 回复语气是否符合品牌调性 · 投诉处理方案是否合理

## Grading Criteria

- [ ] file_created: reply_sheet.md 存在
- [ ] has_ten_replies: 包含 10 条回复（通过 MSG_00x 计数）
- [ ] has_intent_labels: 包含"意图："标注
- [ ] complaint_addressed: MSG_004（投诉）的回复包含道歉词（"抱歉""对不起""非常遗憾"）
- [ ] media_redirected: MSG_008（媒体合作）的回复包含联系方式引导词（"联系""邮件""转接"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "reply_sheet.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_ten_replies","has_intent_labels",
                                   "complaint_addressed","media_redirected"]}
    content = f.read_text(encoding="utf-8")
    msg_refs = re.findall(r'MSG_0\d\d', content)
    has_ten  = len(set(msg_refs)) >= 10
    has_intent = "意图" in content or "类型" in content
    # 找 MSG_004 前后的内容
    m004_match = re.search(r'MSG_004.{0,200}', content, re.DOTALL)
    m004_text  = m004_match.group(0) if m004_match else ""
    complaint_ok = any(w in m004_text for w in ["抱歉","对不起","非常遗憾","感到歉意","很遗憾"])
    m008_match = re.search(r'MSG_008.{0,200}', content, re.DOTALL)
    m008_text  = m008_match.group(0) if m008_match else ""
    media_ok = any(w in m008_text for w in ["联系","邮件","转接","负责人","市场部","pr@","400"])
    return {
        "file_created":        1.0,
        "has_ten_replies":     1.0 if has_ten else 0.0,
        "has_intent_labels":   1.0 if has_intent else 0.0,
        "complaint_addressed": 1.0 if complaint_ok else 0.0,
        "media_redirected":    1.0 if media_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 意图识别准确率 · 回复语气是否符合品牌调性 · 投诉处理方案是否合理意图识别准确率 · 回复语气是否符合品牌调性 · 投诉处理方案是否合理

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
