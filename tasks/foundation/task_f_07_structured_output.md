---
id: task_f_07_structured_output
name: "task_f_07_structured_output"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files: []
dataset_dir: dataset/foundation/task_f_07_structured_output
---

## Prompt

请将以下非结构化信息转换为 JSON 格式，保存到 `output.json`：

> 用户张三，男，28岁，职业是产品经理，所在城市北京，注册时间2025年6月15日，会员等级黄金。

JSON 必须包含以下字段：name, gender, age, occupation, city, register_date, membership

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`: output.json 是否存在
- `valid_json`: 是否为合法 JSON
- `has_all_fields`: 是否包含全部 7 个字段
- `age_is_int`: age 字段是否为整数（不评估具体取值）

## Grading Criteria

- [ ] file_created: output.json 是否存在
- [ ] valid_json: 是否为合法 JSON
- [ ] has_all_fields: 是否包含全部 7 个字段
- [ ] age_is_int: age 字段是否为整数（不评估具体取值）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import json
    f = workspace_path / "output.json"
    if not f.exists(): return {"file_created":0.0,"valid_json":0.0,"has_all_fields":0.0,"age_is_int":0.0}
    try:
        data = json.loads(f.read_text(encoding="utf-8",errors="ignore"))
        required = ["name","gender","age","occupation","city","register_date","membership"]
        has_all = all(k in data for k in required)
        age_val = data.get("age", None)
        age_is_int = isinstance(age_val, int)
        return {"file_created":1.0,"valid_json":1.0,"has_all_fields":1.0 if has_all else 0.0,"age_is_int":1.0 if age_is_int else 0.0}
    except:
        return {"file_created":1.0,"valid_json":0.0,"has_all_fields":0.0,"age_is_int":0.0}
```
