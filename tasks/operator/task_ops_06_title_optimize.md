---
id: task_ops_06_title_optimize
name: "标题党优化（同一内容生成10个差异化标题备选）"
category: operator
grading_type: hybrid
timeout_seconds: 90
workspace_files: []
dataset_dir: dataset/operator/task_ops_06_title_optimize
grading_weights:
  automated: 0.6
  llm_judge: 0.4
---

## Prompt

工作区有一份文章信息 `original.txt`。

请为这篇文章生成 10 个不同风格的标题备选，保存到 `titles.md`。

要求：
- 每个标题独立一行，编号 1-10
- 10 个标题必须风格各异，覆盖以下至少 5 种风格：数字型、疑问型、对比型、痛点型、利益型、悬念型
- 每个标题后用括号注明风格类型
- 字数：每个标题 15-30 字

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：titles.md 存在
- `has_ten_titles`：包含 10 个编号标题
- `has_style_labels`：包含括号内的风格标注
- `has_variety`：包含至少 5 种不同风格关键词（数字/疑问/对比/痛点/利益/悬念/情感）
- `length_ok`：至少 8 个标题字数在 10-35 字之间

**LLM Judge**：标题是否有吸引力 · 风格是否真正差异化（不是换个说法的重复）

## Grading Criteria

- [ ] file_created: titles.md 存在
- [ ] has_ten_titles: 包含 10 个编号标题
- [ ] has_style_labels: 包含括号内的风格标注
- [ ] has_variety: 包含至少 5 种不同风格关键词（数字/疑问/对比/痛点/利益/悬念/情感）
- [ ] length_ok: 至少 8 个标题字数在 10-35 字之间

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "titles.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_ten_titles","has_style_labels","has_variety","length_ok"]}
    content = f.read_text(encoding="utf-8")
    numbered = re.findall(r'^\s*(?:\d{1,2}[\.、\)]|[①-⑩])\s*.+', content, re.MULTILINE)
    has_labels = bool(re.search(r'[（(][^）)]{2,8}[）)]', content))
    styles = ["数字","疑问","对比","痛点","利益","悬念","情感","干货","故事","反常"]
    found_styles = sum(1 for s in styles if s in content)
    # 检查字数
    long_enough = sum(1 for t in numbered if 10 <= len(re.sub(r'[（(][^）)]*[）)]','',t).strip()) <= 40)
    return {
        "file_created":    1.0,
        "has_ten_titles":  1.0 if len(numbered) >= 10 else 0.0,
        "has_style_labels":1.0 if has_labels else 0.0,
        "has_variety":     1.0 if found_styles >= 5 else 0.0,
        "length_ok":       1.0 if long_enough >= 8 else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：标题是否有吸引力 · 风格是否真正差异化（不是换个说法的重复）

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
