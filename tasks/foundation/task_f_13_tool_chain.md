---
id: task_f_13_tool_chain
name: "task_f_13_tool_chain"
category: foundation
grading_type: automated
timeout_seconds: 180
workspace_files:
  - budget.txt
dataset_dir: dataset/foundation/task_f_13_tool_chain
---

## Prompt

请完成以下需要多工具串联的任务：

1. 搜索「特斯拉 Model 3 2026款价格」
2. 读取工作区文件 `budget.txt`
3. 根据搜索结果和预算，判断是否负担得起
4. 将判断结果和依据写入 `conclusion.txt`

## Expected Behavior

The agent should read `budget.txt` (30 万元预算), combine with a Tesla Model 3 price signal from search, and write a reasoned `conclusion.txt`. Automated checks verify that the conclusion references the task subject (特斯拉 / Model 3), the budget file content, and a clear affordability stance—reducing credit for empty or generic text.

Evaluation criteria:
- `conclusion_created`: conclusion.txt 是否存在
- `task_keyword_hit_rate`: 是否覆盖「特斯拉 / Model 3 / 预算金额 / 结论倾向」等金标维度

## Grading Criteria

- [ ] conclusion_created: conclusion.txt 是否存在
- [ ] task_keyword_hit_rate: 关键词组命中率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "conclusion.txt"

    if not f.exists():
        return {"conclusion_created": 0.0, "task_keyword_hit_rate": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    cl = content.lower()

    GROUPS = [
        ("特斯拉", "tesla", "model 3", "model3"),
        ("30万", "三十万", "300000", "30 万"),
        ("负担", "买得起", "超出", "预算", "够", "不够", "可以", "不能", "afford"),
    ]

    def hit(syns):
        return any((s in content) or (s in cl) for s in syns)

    hits = sum(1 for syns in GROUPS if hit(syns))
    hit_rate = hits / len(GROUPS)

    return {
        "conclusion_created": 1.0,
        "task_keyword_hit_rate": round(hit_rate, 2),
    }
```
