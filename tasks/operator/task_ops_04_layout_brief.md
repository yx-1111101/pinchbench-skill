---
id: task_ops_04_layout_brief
name: "图文排版指令生成（给设计师的排版说明书）"
category: operator
grading_type: llm_judge
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/operator/task_ops_04_layout_brief
---

## Prompt

工作区有一篇准备发布到小红书的文章 `article_content.txt`。

请根据文章内容，生成一份给设计师的**图文排版指令** `layout_brief.md`，要求：

- 共 9 张图（小红书标准图数）
- 每张图：说明图的用途、主要文字内容、视觉风格建议（配色/排版/元素）
- 封面图（第1张）要特别说明标题文案和视觉重点
- 整体风格：简洁职场感，不严肃，轻松有设计感
- 最后给出配色方案建议（3种颜色+用途）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：layout_brief.md 存在
- `file_not_empty`：内容超过 300 字
- `has_nine_slides`：包含 9 张图的描述（通过"第1张""图1""slide 1"等识别）
- `has_cover_spec`：包含封面相关描述（"封面""第1张""首图"）
- `has_color_scheme`：包含颜色相关词（"配色""颜色""色调""#"）

**LLM Judge**：排版指令是否清晰可执行 · 内容与文章是否对应 · 视觉风格是否统一且符合平台调性

## Grading Criteria

- [ ] file_created: layout_brief.md 存在
- [ ] file_not_empty: 内容超过 300 字
- [ ] has_nine_slides: 包含 9 张图的描述（通过"第1张""图1""slide 1"等识别）
- [ ] has_cover_spec: 包含封面相关描述（"封面""第1张""首图"）
- [ ] has_color_scheme: 包含颜色相关词（"配色""颜色""色调""#"）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "layout_brief.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","file_not_empty","has_nine_slides","has_cover_spec","has_color_scheme"]}
    content = f.read_text(encoding="utf-8")
    slide_refs = re.findall(r'(?:第[一二三四五六七八九1-9]张|图[1-9]|Slide\s*[1-9]|第\s*[1-9]\s*[张页])', content)
    has_nine   = len(set(slide_refs)) >= 6
    has_cover  = any(w in content for w in ["封面","第一张","第1张","首图","cover"])
    has_color  = any(w in content for w in ["配色","颜色","色调","#","RGB","主色","辅助色"])
    return {
        "file_created":    1.0,
        "file_not_empty":  1.0 if len(content.strip()) > 300 else 0.0,
        "has_nine_slides": 1.0 if has_nine else 0.0,
        "has_cover_spec":  1.0 if has_cover else 0.0,
        "has_color_scheme":1.0 if has_color else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：排版指令是否清晰可执行 · 内容与文章是否对应 · 视觉风格是否统一且符合平台调性

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
