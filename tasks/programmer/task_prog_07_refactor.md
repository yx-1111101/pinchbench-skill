---
id: task_prog_07_refactor
name: "代码重构（上帝函数拆分 + 可读性提升）"
category: programmer
grading_type: hybrid
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/programmer/task_prog_07_refactor
grading_weights:
  automated: 0.6
  llm_judge: 0.4
---

## Prompt

工作区有一个 `order_processor.py`，其中 `process_order()` 是一个 180 行的上帝函数，揉合了校验、计算、数据库写入、邮件通知等逻辑。

请重构这个文件：
1. 将 `process_order()` 拆分为若干职责单一的小函数
2. 每个函数不超过 30 行
3. 保持对外接口不变（`process_order(order_dict)` 签名不变）
4. 保存为同名文件

工作区同时有测试文件 `test_order.py`，重构后必须全部通过。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `tests_pass`：`pytest test_order.py` 全部通过（行为不变）
- `no_god_function`：不存在超过 35 行的函数
- `function_count_increased`：函数数量 ≥ 5（原来只有1个）
- `interface_preserved`：仍包含 `def process_order(` 签名

**LLM Judge**：拆分是否符合单一职责 · 命名是否语义清晰 · 整体可读性提升程度

## Grading Criteria

- [ ] tests_pass: `pytest test_order.py` 全部通过（行为不变）
- [ ] no_god_function: 不存在超过 35 行的函数
- [ ] function_count_increased: 函数数量 ≥ 5（原来只有1个）
- [ ] interface_preserved: 仍包含 `def process_order(` 签名

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import subprocess, ast, re
    f = workspace_path / "order_processor.py"
    test_f = workspace_path / "test_order.py"
    if not f.exists():
        return {k: 0.0 for k in ["tests_pass","no_god_function","function_count_increased","interface_preserved"]}
    code = f.read_text(encoding="utf-8")

    tests_pass = False
    if test_f.exists():
        try:
            r = subprocess.run(["python","-m","pytest",str(test_f),"-q","--tb=no"],
                capture_output=True, text=True, timeout=60, cwd=str(workspace_path))
            tests_pass = r.returncode == 0
        except Exception: pass

    no_god = True
    func_count = 0
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
                lines = node.end_lineno - node.lineno
                if lines > 35: no_god = False
    except Exception: pass

    iface_ok = "def process_order(" in code
    return {
        "tests_pass":              1.0 if tests_pass else 0.0,
        "no_god_function":         1.0 if no_god else 0.0,
        "function_count_increased":1.0 if func_count >= 5 else 0.0,
        "interface_preserved":     1.0 if iface_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：拆分是否符合单一职责 · 命名是否语义清晰 · 整体可读性提升程度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
