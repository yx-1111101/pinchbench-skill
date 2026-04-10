---
id: task_prog_12_cicd_gen
name: "CI/CD 配置生成（GitHub Actions workflow）"
category: programmer
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/programmer/task_prog_12_cicd_gen
---

## Prompt

工作区有一份项目说明 `project_info.md`。

请生成 `.github/workflows/ci.yml`，实现：
1. 触发条件：push 到 main 分支 或 PR
2. 运行环境：ubuntu-latest，Python 3.11
3. 步骤：checkout → 安装依赖 → 运行 pytest → 构建 Docker 镜像
4. 环境变量：通过 secrets 注入 `DATABASE_URL`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：.github/workflows/ci.yml 存在
- `valid_yaml`：YAML 语法合法
- `has_trigger`：包含 push/pull_request 触发器
- `has_python_311`：包含 `python-version` 且为 3.11
- `has_pytest_step`：包含 pytest 运行步骤
- `has_docker_step`：包含 docker build 步骤
- `uses_secrets`：DATABASE_URL 通过 `secrets.` 注入

## Grading Criteria

- [ ] file_created: .github/workflows/ci.yml 存在
- [ ] valid_yaml: YAML 语法合法
- [ ] has_trigger: 包含 push/pull_request 触发器
- [ ] has_python_311: 包含 `python-version` 且为 3.11
- [ ] has_pytest_step: 包含 pytest 运行步骤
- [ ] has_docker_step: 包含 docker build 步骤
- [ ] uses_secrets: DATABASE_URL 通过 `secrets.` 注入

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    ci_paths = [
        workspace_path / ".github" / "workflows" / "ci.yml",
        workspace_path / "ci.yml",
    ]
    f = next((p for p in ci_paths if p.exists()), None)
    if not f:
        return {k: 0.0 for k in ["file_created","valid_yaml","has_trigger","has_python_311",
                                   "has_pytest_step","has_docker_step","uses_secrets"]}
    text = f.read_text(encoding="utf-8")
    valid_yaml = True
    try:
        import yaml; yaml.safe_load(text)
    except Exception: valid_yaml = False
    return {
        "file_created":    1.0,
        "valid_yaml":      1.0 if valid_yaml else 0.0,
        "has_trigger":     1.0 if bool(re.search(r'push|pull_request', text)) else 0.0,
        "has_python_311":  1.0 if "3.11" in text else 0.0,
        "has_pytest_step": 1.0 if "pytest" in text else 0.0,
        "has_docker_step": 1.0 if bool(re.search(r'docker\s+build', text)) else 0.0,
        "uses_secrets":    1.0 if bool(re.search(r'secrets\.', text)) else 0.0,
    }
```
