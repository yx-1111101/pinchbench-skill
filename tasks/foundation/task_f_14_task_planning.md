---
id: task_f_14_task_planning
name: "task_f_14_task_planning"
category: foundation
grading_type: automated
timeout_seconds: 270
workspace_files: []
dataset_dir: dataset/foundation/task_f_14_task_planning
---

## Prompt

我需要「下周一在上海举办一场50人的产品发布会」，但我完全不知道从哪里开始。

请帮我制定一份详细的执行计划，保存到 `plan.md`，要求：
- 拆解为具体可执行的子任务
- 每个子任务标注负责方向和预计耗时
- 按时间顺序排列（倒推法，从发布会当天往前排）

## Expected Behavior

The agent should produce a structured plan in `plan.md`. Automated grading checks list/time ordering **and** that the plan explicitly reflects the task brief (上海、50 人、发布会、时间倒推等)，避免泛泛长文混分。

Evaluation criteria:
- `file_created`: plan.md 是否存在
- `has_subtasks`: 是否有至少 5 个子任务线索
- `has_timeline`: 是否有时间信息（天/小时/周）
- `is_ordered`: 是否有顺序结构（数字列表或时间排序）
- `brief_keyword_hit_rate`: Prompt 金标要素命中比例（0–1）

## Grading Criteria

- [ ] file_created: plan.md 是否存在
- [ ] has_subtasks: 是否有至少 5 个子任务
- [ ] has_timeline: 是否有时间信息
- [ ] is_ordered: 是否有顺序结构
- [ ] brief_keyword_hit_rate: 任务要素关键词命中率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re

    f = workspace_path / "plan.md"
    if not f.exists():
        return {
            k: 0.0
            for k in [
                "file_created",
                "has_subtasks",
                "has_timeline",
                "is_ordered",
                "brief_keyword_hit_rate",
            ]
        }

    c = f.read_text(encoding="utf-8", errors="ignore")
    cl = c.lower()

    subtasks = len(re.findall(r"^[-\d]", c, re.M))
    has_time = bool(re.search(r"\d+天|\d+小时|\d+周|天前|提前", c))
    is_ordered = bool(re.search(r"^[1-9]\.", c, re.M)) or bool(re.search(r"第[一二三四五六七八九十]", c))

    GROUPS = [
        ("上海",),
        ("50", "五十"),
        ("发布", "发布会"),
        ("周一", "星期", "礼拜"),
        ("产品",),
    ]
    hits = sum(1 for syns in GROUPS if any(s in c or s in cl for s in syns))
    hit_rate = hits / len(GROUPS)

    return {
        "file_created": 1.0,
        "has_subtasks": 1.0 if subtasks >= 5 else 0.0,
        "has_timeline": 1.0 if has_time else 0.0,
        "is_ordered": 1.0 if is_ordered else 0.0,
        "brief_keyword_hit_rate": round(hit_rate, 2),
    }
```
