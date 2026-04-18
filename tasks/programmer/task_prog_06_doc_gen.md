---
id: task_prog_06_doc_gen
name: "技术文档生成（docstring + README）"
category: programmer
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - processor.py
dataset_dir: dataset/programmer/task_prog_06_doc_gen
grading_weights:
  automated: 0.3
  llm_judge: 0.7
---

## Prompt

工作区有一个裸模块 `processor.py`，所有函数均无注释，也没有 README。

请完成以下两件事：
1. 为 `processor.py` 中每个函数补全 Google-style docstring（包含 Args、Returns、Raises、Example）
2. 生成 `README.md`，包含：模块用途说明、安装/依赖、函数速查表、使用示例

将修改后的 `processor.py` 和新生成的 `README.md` 都保存到工作区。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `processor_modified`：processor.py 存在且包含明显新增文档内容（文件长度 > 800）
- `readme_created`：README.md 存在
- `has_docstrings`：processor.py 包含 docstring（含 `"""`）
- `has_args_section`：docstring 包含 `Args:` 字段
- `readme_has_table`：README.md 包含 Markdown 表格（`|` 字符）

**LLM Judge**：docstring 准确性 · 示例是否可运行 · README 结构完整度

## Grading Criteria

- [ ] processor_modified: processor.py 存在且包含明显新增文档内容（文件长度 > 800）
- [ ] readme_created: README.md 存在
- [ ] has_docstrings: processor.py 包含 docstring（含 `"""`）
- [ ] has_args_section: docstring 包含 `Args:` 字段
- [ ] readme_has_table: README.md 包含 Markdown 表格（`|` 字符）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    proc = workspace_path / "processor.py"
    readme = workspace_path / "README.md"
    proc_ok = proc.exists() and len(proc.read_text(encoding="utf-8")) > 800
    readme_ok = readme.exists()
    proc_text = proc.read_text(encoding="utf-8") if proc.exists() else ""
    readme_text = readme.read_text(encoding="utf-8") if readme_ok else ""
    return {
        "processor_modified": 1.0 if proc_ok else 0.0,
        "readme_created":     1.0 if readme_ok else 0.0,
        "has_docstrings":     1.0 if '"""' in proc_text or "'''" in proc_text else 0.0,
        "has_args_section":   1.0 if "Args:" in proc_text else 0.0,
        "readme_has_table":   1.0 if "|" in readme_text else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: docstring 准确性 · 示例是否可运行 · README 结构完整度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
