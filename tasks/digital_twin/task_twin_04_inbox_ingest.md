---
id: task_twin_04_inbox_ingest
name: "持续学习 — 多形态碎片输入 → 无感结构化存库"
category: digital_twin
grading_type: hybrid
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/digital_twin/task_twin_04_inbox_ingest
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有 `inbox.txt`，记录了陈默今天随手丢进来的7条输入（有URL、一句话灵感、文章摘录、会议语音转文字，格式各异）。

请处理所有输入，生成 `knowledge_cards.json`，每条输入对应一张卡片：

```json
[
  {
    "id": "card_001",
    "source_type": "article|url|voice|idea|document",
    "title": "自动生成的标题",
    "summary": "50字以内摘要",
    "tags": ["标签1", "标签2"],
    "category": "行业资讯|个人灵感|待执行|参考资料|人际关系",
    "action_required": true
  }
]
```

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：knowledge_cards.json 存在
- `valid_json`：合法 JSON
- `has_seven_cards`：包含7张卡片
- `all_have_tags`：每张卡片都有非空 tags
- `categories_varied`：使用了至少3种不同 category 值
- `action_flags_present`：每张卡片都有 action_required 字段

**LLM Judge**：摘要质量 · 分类是否准确 · 对碎片灵感的处理是否合理

## Grading Criteria

- [ ] file_created: knowledge_cards.json 存在
- [ ] valid_json: 合法 JSON
- [ ] has_seven_cards: 包含7张卡片
- [ ] all_have_tags: 每张卡片都有非空 tags
- [ ] categories_varied: 使用了至少3种不同 category 值
- [ ] action_flags_present: 每张卡片都有 action_required 字段

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import json
    f = workspace_path / "knowledge_cards.json"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","valid_json","has_seven_cards",
                                   "all_have_tags","categories_varied","action_flags_present"]}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except:
        return {"file_created":1.0,"valid_json":0.0,"has_seven_cards":0.0,
                "all_have_tags":0.0,"categories_varied":0.0,"action_flags_present":0.0}
    has_seven    = isinstance(data, list) and len(data) >= 7
    all_tags     = has_seven and all(isinstance(c.get("tags"), list) and len(c["tags"]) > 0 for c in data)
    categories   = set(c.get("category","") for c in data) if has_seven else set()
    action_flags = has_seven and all("action_required" in c for c in data)
    return {
        "file_created":         1.0,
        "valid_json":           1.0,
        "has_seven_cards":      1.0 if has_seven else 0.0,
        "all_have_tags":        1.0 if all_tags else 0.0,
        "categories_varied":    1.0 if len(categories) >= 3 else 0.0,
        "action_flags_present": 1.0 if action_flags else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：摘要质量 · 分类是否准确 · 对碎片灵感的处理是否合理

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
