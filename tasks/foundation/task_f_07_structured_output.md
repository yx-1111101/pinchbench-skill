---
id: task_f_07_structured_output
name: "task_f_07_structured_output"
category: foundation
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/foundation/task_f_07_structured_output
---

## Prompt

请将以下非结构化信息转换为 JSON 格式，保存到 `output.json`：

> 用户张三，男，28岁，职业是产品经理，所在城市北京，注册时间2025年6月15日，会员等级黄金。

JSON 必须包含以下字段：name, gender, age, occupation, city, register_date, membership

## Expected Behavior

The agent should emit valid JSON with the seven required keys and **correct values** drawn from the prompt (not placeholders). Automated checks verify field presence, types, and a normalized match against the golden values below.

Evaluation criteria:
- `file_created`: output.json 是否存在
- `valid_json`: 是否为合法 JSON
- `has_all_fields`: 是否包含全部 7 个字段
- `age_is_int`: age 是否为整数类型
- `value_correctness_rate`: 各字段与金标一致的比例（0–1）

## Grading Criteria

- [ ] file_created: output.json 是否存在
- [ ] valid_json: 是否为合法 JSON
- [ ] has_all_fields: 是否包含全部 7 个字段
- [ ] age_is_int: age 是否为整数
- [ ] value_correctness_rate: 字段值正确率

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import json
    import re

    f = workspace_path / "output.json"
    if not f.exists():
        return {
            "file_created": 0.0,
            "valid_json": 0.0,
            "has_all_fields": 0.0,
            "age_is_int": 0.0,
            "value_correctness_rate": 0.0,
        }

    try:
        data = json.loads(f.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return {
            "file_created": 1.0,
            "valid_json": 0.0,
            "has_all_fields": 0.0,
            "age_is_int": 0.0,
            "value_correctness_rate": 0.0,
        }

    required = ["name", "gender", "age", "occupation", "city", "register_date", "membership"]
    has_all = all(k in data for k in required)
    age_val = data.get("age", None)
    age_is_int = isinstance(age_val, int)

    def ok_name(v):
        return "张三" in str(v)

    def ok_gender(v):
        s = str(v).strip()
        return s in ("男", "M", "m", "male", "Male")

    def ok_age(v):
        return v == 28 or str(v).strip() == "28"

    def ok_occ(v):
        return "产品经理" in str(v)

    def ok_city(v):
        return "北京" in str(v)

    def ok_reg(v):
        s = str(v)
        return bool(
            re.search(r"2025[-/]0?6[-/]0?15", s)
            or re.search(r"2025\s*年\s*0?6\s*月\s*0?15", s)
        )

    def ok_mem(v):
        return "黄金" in str(v)

    checks = [
        ok_name(data.get("name")),
        ok_gender(data.get("gender")),
        ok_age(age_val),
        ok_occ(data.get("occupation")),
        ok_city(data.get("city")),
        ok_reg(data.get("register_date")),
        ok_mem(data.get("membership")),
    ]
    rate = sum(1.0 for x in checks if x) / len(checks)

    return {
        "file_created": 1.0,
        "valid_json": 1.0,
        "has_all_fields": 1.0 if has_all else 0.0,
        "age_is_int": 1.0 if age_is_int else 0.0,
        "value_correctness_rate": round(rate, 2),
    }
```
