---
id: task_f_08_markdown_output
name: "task_f_08_markdown_output"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_08_markdown_output
---

## Prompt

请生成一份 Markdown 格式的「AI 工具对比报告」，**必须围绕以下三款工具展开对比**：ChatGPT、Claude、Gemini。保存到 `report.md`，且必须包含：

1. 一级标题（# 开头）
2. 至少两个二级标题（## 开头）
3. 一个 Markdown 表格（至少 3 列 3 行），且表格中需出现上述三款工具名称
4. 一个无序列表（- 开头，至少 3 项）

## Expected Behavior

The agent should produce `report.md` with valid Markdown structure and **explicitly cover ChatGPT, Claude, and Gemini** so that automated checks can verify tool names and format constraints.

Evaluation criteria:
- `file_created`: report.md 是否存在
- `has_h1` / `has_h2` / `has_table` / `has_list`: 结构约束
- `tool_keyword_hit_rate`: 三款工具名称在全文中的命中比例（0–1）

## Grading Criteria

- [ ] file_created: report.md 是否存在
- [ ] has_h1: 是否有一级标题
- [ ] has_h2: 是否有至少 2 个二级标题
- [ ] has_table: 是否有 Markdown 表格
- [ ] has_list: 是否有无序列表（≥3 项）
- [ ] tool_keyword_hit_rate: ChatGPT / Claude / Gemini 是否均被提及

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re

    f = workspace_path / "report.md"
    if not f.exists():
        return {
            k: 0.0
            for k in [
                "file_created",
                "has_h1",
                "has_h2",
                "has_table",
                "has_list",
                "tool_keyword_hit_rate",
            ]
        }

    c = f.read_text(encoding="utf-8", errors="ignore")
    cl = c.lower()

    tools = [
        ("chatgpt", "gpt"),
        ("claude",),
        ("gemini",),
    ]
    hits = sum(1 for syns in tools if any(s in cl for s in syns))
    hit_rate = hits / len(tools)

    return {
        "file_created": 1.0,
        "has_h1": 1.0 if re.search(r"^# [^#]", c, re.M) else 0.0,
        "has_h2": 1.0 if len(re.findall(r"^## ", c, re.M)) >= 2 else 0.0,
        "has_table": 1.0 if re.search(r"^\|.+\|.+\|", c, re.M) else 0.0,
        "has_list": 1.0 if len(re.findall(r"^[-*] ", c, re.M)) >= 3 else 0.0,
        "tool_keyword_hit_rate": round(hit_rate, 2),
    }
```
