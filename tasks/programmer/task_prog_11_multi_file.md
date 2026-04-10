---
id: task_prog_11_multi_file
name: "多文件协作修改（接口变更跨文件传播）"
category: programmer
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/programmer/task_prog_11_multi_file
---

## Prompt

工作区有一个小型 Python 项目，包含3个互相依赖的文件：
- `models.py`：User 数据模型
- `service.py`：业务逻辑层，依赖 models
- `api.py`：接口层，依赖 service

现在需求变更：**User 模型新增 `phone` 字段（必填），同时 `create_user()` 函数签名需要加入 `phone` 参数。**

请在所有相关文件中传播这个变更，然后运行工作区的 `test_integration.py` 确保测试通过。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `tests_pass`：`pytest test_integration.py` 全部通过
- `models_updated`：models.py 包含 `phone` 字段
- `service_updated`：service.py 中 `create_user` 签名包含 `phone`
- `api_updated`：api.py 中传递了 `phone` 参数
- `all_three_modified`：三个文件都有修改（均包含 `phone`）

## Grading Criteria

- [ ] tests_pass: `pytest test_integration.py` 全部通过
- [ ] models_updated: models.py 包含 `phone` 字段
- [ ] service_updated: service.py 中 `create_user` 签名包含 `phone`
- [ ] api_updated: api.py 中传递了 `phone` 参数
- [ ] all_three_modified: 三个文件都有修改（均包含 `phone`）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import subprocess
    models  = workspace_path / "models.py"
    service = workspace_path / "service.py"
    api     = workspace_path / "api.py"
    test_f  = workspace_path / "test_integration.py"

    def has_phone(p): return p.exists() and "phone" in p.read_text(encoding="utf-8")

    tests_pass = False
    if test_f.exists():
        try:
            r = subprocess.run(["python","-m","pytest",str(test_f),"-q","--tb=no"],
                capture_output=True, text=True, timeout=60, cwd=str(workspace_path))
            tests_pass = r.returncode == 0
        except Exception: pass

    m_ok = has_phone(models)
    s_ok = has_phone(service)
    a_ok = has_phone(api)
    return {
        "tests_pass":       1.0 if tests_pass else 0.0,
        "models_updated":   1.0 if m_ok else 0.0,
        "service_updated":  1.0 if s_ok else 0.0,
        "api_updated":      1.0 if a_ok else 0.0,
        "all_three_modified":1.0 if (m_ok and s_ok and a_ok) else 0.0,
    }
```
