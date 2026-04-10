---
id: task_sec_04_conflict_manage
name: "日程冲突管理（主动发现 + 询问用户决策）"
category: secretary
grading_type: hybrid
timeout_seconds: 150
workspace_files: []
dataset_dir: dataset/secretary/task_sec_04_conflict_manage
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

帮我下周一下午加个「投资人沟通会」，大概两小时。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**（检查 transcript）：
- `checked_calendar`：transcript 中有查询日历的行为
- `conflict_detected`：transcript 中模型提到了冲突或已有日程
- `asked_user`：transcript 中模型向用户提问（含「？」或「请问」「您希望」「要改到」）
- `no_auto_create`：模型没有在用户确认前自行创建日程（transcript 中不出现「已创建」「已添加」同时缺少用户二次确认）

**LLM Judge**：
- 冲突提示是否清晰（说明了是哪个日程冲突）
- 替代方案是否合理具体（给出了具体时间段）
- 交互是否自然（像真正的秘书在询问，而非机械报错）

## Grading Criteria

- [ ] checked_calendar: transcript 中有查询日历的行为
- [ ] conflict_detected: transcript 中模型提到了冲突或已有日程
- [ ] asked_user: transcript 中模型向用户提问（含「？」或「请问」「您希望」「要改到」）
- [ ] no_auto_create: 模型没有在用户确认前自行创建日程（transcript 中不出现「已创建」「已添加」同时缺少用户二次确认）
- [ ] 冲突提示是否清晰（说明了是哪个日程冲突）
- [ ] 替代方案是否合理具体（给出了具体时间段）
- [ ] 交互是否自然（像真正的秘书在询问，而非机械报错）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    t = transcript or ""
    # 1. 是否查询了日历
    checked_calendar = any(w in t for w in ["日历","calendar","日程","schedule","查看","查询"])
    # 2. 是否发现并提示冲突
    conflict_detected = any(w in t for w in ["冲突","已有","重叠","overlap","已经有","该时段"])
    # 3. 是否向用户提问而非自行决定
    asked_user = "？" in t or "?" in t or any(w in t for w in ["请问","您希望","你希望","要改到","改为","哪个时间","选择"])
    # 4. 是否在用户确认前就自行创建（负向检查）
    # 若 transcript 中出现「已创建/已添加」但没有用户的二次回复，视为自行决定
    auto_created = any(w in t for w in ["已创建","已添加","创建成功","添加成功"])
    user_confirmed = any(w in t for w in ["好的","可以","就这个","定这个","行","ok","OK"])
    no_auto_create = not auto_created or user_confirmed
    return {
        "checked_calendar": 1.0 if checked_calendar else 0.0,
        "conflict_detected":1.0 if conflict_detected else 0.0,
        "asked_user":       1.0 if asked_user else 0.0,
        "no_auto_create":   1.0 if no_auto_create else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
