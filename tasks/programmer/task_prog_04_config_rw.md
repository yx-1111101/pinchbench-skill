---
id: task_prog_04_config_rw
name: "配置文件读取与修改"
category: programmer
grading_type: automated
timeout_seconds: 360
workspace_files:
  - settings.json
  - deploy.yaml
dataset_dir: dataset/programmer/task_prog_04_config_rw
---

## Prompt

工作区有两个配置文件：

- `settings.json`：服务运行配置
- `deploy.yaml`：部署环境配置

请完成以下修改并保存：

**settings.json 修改项**：
- 将 `host` 改为 `0.0.0.0`
- 将 `database.port` 改为 `5433`
- 将 `log_level` 改为 `WARNING`
- 将 `api.timeout` 改为 `60`

**deploy.yaml 修改项**：
- 将 `environment.host` 改为 `prod.example.com`
- 将 `environment.db_url` 改为 `postgres://prod:5432/app`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `settings_host_updated`：settings.json 中 host == "0.0.0.0"
- `settings_db_updated`：database.port == 5433
- `settings_loglevel_updated`：log_level == "WARNING"
- `settings_api_updated`：api.timeout == 60
- `yaml_host_updated`：deploy.yaml 中 host 包含 prod.example.com
- `yaml_db_updated`：db_url 包含 prod:5432

## Grading Criteria

- [ ] settings_host_updated: settings.json 中 host == "0.0.0.0"
- [ ] settings_db_updated: database.port == 5433
- [ ] settings_loglevel_updated: log_level == "WARNING"
- [ ] settings_api_updated: api.timeout == 60
- [ ] yaml_host_updated: deploy.yaml 中 host 包含 prod.example.com
- [ ] yaml_db_updated: db_url 包含 prod:5432

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import json, re
    results = {}
    sj = workspace_path / "settings.json"
    dy = workspace_path / "deploy.yaml"

    if sj.exists():
        try:
            cfg = json.loads(sj.read_text(encoding="utf-8"))
            results["settings_host_updated"]    = 1.0 if cfg.get("host") == "0.0.0.0" else 0.0
            results["settings_db_updated"]      = 1.0 if str(cfg.get("database", {}).get("port","")) == "5433" else 0.0
            results["settings_loglevel_updated"]= 1.0 if cfg.get("log_level") == "WARNING" else 0.0
            results["settings_api_updated"]     = 1.0 if str(cfg.get("api", {}).get("timeout","")) == "60" else 0.0
        except:
            for k in ["settings_host_updated","settings_db_updated","settings_loglevel_updated","settings_api_updated"]:
                results[k] = 0.0
    else:
        for k in ["settings_host_updated","settings_db_updated","settings_loglevel_updated","settings_api_updated"]:
            results[k] = 0.0

    if dy.exists():
        yc = dy.read_text(encoding="utf-8")
        results["yaml_host_updated"] = 1.0 if "prod.example.com" in yc else 0.0
        results["yaml_db_updated"]   = 1.0 if "prod:5432" in yc else 0.0
    else:
        results["yaml_host_updated"] = 0.0
        results["yaml_db_updated"]   = 0.0
    return results
```
