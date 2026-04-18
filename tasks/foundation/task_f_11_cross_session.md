---
id: task_f_11_cross_session
name: "task_f_11_cross_session"
category: foundation
grading_type: automated
timeout_seconds: 270
workspace_files: []
dataset_dir: dataset/foundation/task_f_11_cross_session
---

## Prompt

这是一个跨会话记忆测试，分两步执行：

**步骤 1（第一次运行）**：
请记住以下信息，存入持久化记忆：「用户偏好：早上9点的简报，不喜欢长篇大论，偏好要点式输出」

**步骤 2（第二次运行）**：
请从记忆中检索用户偏好，生成一份符合偏好的今日简报，保存到 `brief.txt`

## Expected Behavior

The agent should retrieve the stated preferences and reflect them in `brief.txt`. Automated grading **cannot** verify external memory APIs; it only checks whether `brief.txt` mentions the preference cues (9 点简报、要点式、避免长篇等). This is the same “ground-truth keyword” pattern as `task_f_02` / `task_f_01`.

Evaluation criteria:
- `brief_created`: brief.txt 是否存在
- `preference_keyword_hit_rate`: 用户偏好关键词组命中比例（0–1）

## Grading Criteria

- [ ] brief_created: brief.txt 是否存在
- [ ] preference_keyword_hit_rate: 偏好关键词命中率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    brief = workspace_path / "brief.txt"
    if not brief.exists():
        return {"brief_created": 0.0, "preference_keyword_hit_rate": 0.0}

    c = brief.read_text(encoding="utf-8", errors="ignore").strip()
    cl = c.lower()

    # From prompt: 早上9点的简报；不喜欢长篇大论；要点式输出
    GROUPS = [
        ("9点", "九点", "09:00", "9:00", "早上9"),
        ("简报", "晨报", "摘要", "要闻"),
        ("要点", "bullet", "条目", "简洁", "简短", "精炼"),
        ("长篇", "冗长", "啰嗦"),
    ]

    hits = sum(
        1
        for syns in GROUPS
        if any((s in c) or (s in cl) for s in syns)
    )
    hit_rate = hits / len(GROUPS)

    return {
        "brief_created": 1.0,
        "preference_keyword_hit_rate": round(hit_rate, 2),
    }
```
