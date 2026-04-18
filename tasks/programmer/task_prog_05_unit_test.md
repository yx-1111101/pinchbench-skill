---
id: task_prog_05_unit_test
name: "单元测试生成（pytest）"
category: programmer
grading_type: automated
timeout_seconds: 150
workspace_files:
  - utils.py
dataset_dir: dataset/programmer/task_prog_05_unit_test
---

## Prompt

工作区有一个工具函数模块 `utils.py`，包含数个边界条件复杂的函数。

请为其生成较完整的 pytest 测试文件 `test_utils.py`，要求：
- 尽量覆盖每个函数的正常路径、边界值、异常输入
- 使用 `pytest.raises` 测试预期异常
- 测试用例有清晰的命名（`test_功能_场景`）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：test_utils.py 存在
- `valid_python`：文件语法合法
- `all_tests_pass`：`pytest test_utils.py` 全部通过（返回码 0）
- `covers_edge_cases`：包含边界/异常测试（`pytest.raises` 或 `None`/`[]`/`0` 等边界值出现）
- `test_count_sufficient`：测试函数数量 ≥ 8

说明：自动评分只验证基础测试完备度代理指标；“是否覆盖全部函数”与“测试质量深度”由人工或 LLM 评审综合判断。

## Grading Criteria

- [ ] file_created: test_utils.py 存在
- [ ] valid_python: 文件语法合法
- [ ] all_tests_pass: `pytest test_utils.py` 全部通过（返回码 0）
- [ ] covers_edge_cases: 包含边界/异常测试（`pytest.raises` 或 `None`/`[]`/`0` 等边界值出现）
- [ ] test_count_sufficient: 测试函数数量 ≥ 8

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import subprocess, ast, re
    f = workspace_path / "test_utils.py"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","valid_python","all_tests_pass",
                                   "covers_edge_cases","test_count_sufficient"]}
    code = f.read_text(encoding="utf-8")
    valid = True
    try: ast.parse(code)
    except SyntaxError: valid = False

    passed = False
    if valid:
        try:
            r = subprocess.run(["python","-m","pytest",str(f),"-q","--tb=no"],
                capture_output=True, text=True, timeout=60, cwd=str(workspace_path))
            passed = r.returncode == 0
        except Exception: pass

    edge = bool(re.search(r'pytest\.raises|None|\\[\\]|,\\s*0\\b|,\\s*-1\\b|empty|边界', code))
    count = len(re.findall(r'^def test_', code, re.MULTILINE))
    return {
        "file_created":         1.0,
        "valid_python":         1.0 if valid else 0.0,
        "all_tests_pass":       1.0 if passed else 0.0,
        "covers_edge_cases":    1.0 if edge else 0.0,
        "test_count_sufficient":1.0 if count >= 8 else (0.5 if count >= 5 else 0.0),
    }
```
