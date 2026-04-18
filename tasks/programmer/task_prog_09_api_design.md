---
id: task_prog_09_api_design
name: "API 接口设计（OpenAPI 规范生成）"
category: programmer
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - prd.md
dataset_dir: dataset/programmer/task_prog_09_api_design
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有一份产品需求文档 `prd.md`，描述了一个「任务管理系统」的核心功能需求。

请根据 PRD 设计 RESTful API，生成 `openapi.yaml`（OpenAPI 3.0 规范），包含：
- 至少 5 个端点（增删改查 + 列表）
- 每个端点的请求体 / 响应 Schema
- 错误码定义（400 / 401 / 404 / 500）
- 认证方式（Bearer Token）

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：openapi.yaml 存在
- `valid_yaml`：YAML 语法合法
- `has_openapi_version`：包含 `openapi: "3.`
- `has_five_paths`：paths 下包含 ≥ 5 个路由
- `has_auth`：包含 Bearer / securitySchemes / Authorization
- `has_error_codes`：包含 400 / 401 / 404 / 500 响应定义

**LLM Judge**：路由设计是否符合 REST 规范 · Schema 是否合理完整 · 与 PRD 需求的覆盖度

## Grading Criteria

- [ ] file_created: openapi.yaml 存在
- [ ] valid_yaml: YAML 语法合法
- [ ] has_openapi_version: 包含 `openapi: "3.`
- [ ] has_five_paths: paths 下包含 ≥ 5 个路由
- [ ] has_auth: 包含 Bearer / securitySchemes / Authorization
- [ ] has_error_codes: 包含 400 / 401 / 404 / 500 响应定义

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "openapi.yaml"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","valid_yaml","has_openapi_version",
                                   "has_five_paths","has_auth","has_error_codes"]}
    text = f.read_text(encoding="utf-8")
    valid_yaml = True
    try:
        import yaml; yaml.safe_load(text)
    except Exception: valid_yaml = False
    has_ver   = bool(re.search(r"openapi:\s*['\"]?3\.", text))
    paths_cnt = len(re.findall(r'^\s{2}/', text, re.MULTILINE))
    has_auth  = any(w in text for w in ["Bearer","bearerAuth","securitySchemes","Authorization"])
    has_err   = all(code in text for code in ["400", "401", "404", "500"])
    return {
        "file_created":       1.0,
        "valid_yaml":         1.0 if valid_yaml else 0.0,
        "has_openapi_version":1.0 if has_ver else 0.0,
        "has_five_paths":     1.0 if paths_cnt >= 5 else 0.0,
        "has_auth":           1.0 if has_auth else 0.0,
        "has_error_codes":    1.0 if has_err else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 路由设计是否符合 REST 规范 · Schema 是否合理完整 · 与 PRD 需求的覆盖度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
