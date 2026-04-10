---
id: task_twin_01_profile_build
name: "冷启动 — 读用户问卷 → 生成结构化人格档案"
category: digital_twin
grading_type: hybrid
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/digital_twin/task_twin_01_profile_build
grading_weights:
  automated: 0.5
  llm_judge: 0.5
---

## Prompt

工作区有用户陈默填写的问卷 `onboarding_survey.txt`。

请阅读问卷，生成结构化人格档案 `persona.json`，必须包含以下字段：

```json
{
  "name": "姓名",
  "role": "职业身份",
  "writing_style": ["风格特征1", "风格特征2"],
  "decision_style": ["决策特征1", "决策特征2"],
  "boundaries": ["边界1", "边界2"],
  "catchphrases": ["口头禅1"],
  "topics_of_interest": ["感兴趣话题1"],
  "avoid": ["不想被替代处理的事1"]
}
```

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：persona.json 存在
- `valid_json`：是合法 JSON
- `has_all_fields`：包含以上8个字段
- `writing_style_not_empty`：writing_style 数组非空（≥2条）
- `boundaries_present`：boundaries 数组非空

**LLM Judge**：提炼是否准确 · 风格描述是否具体可操作 · 边界是否清晰

## Grading Criteria

- [ ] file_created: persona.json 存在
- [ ] valid_json: 是合法 JSON
- [ ] has_all_fields: 包含以上8个字段
- [ ] writing_style_not_empty: writing_style 数组非空（≥2条）
- [ ] boundaries_present: boundaries 数组非空

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import json
    f = workspace_path / "persona.json"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","valid_json","has_all_fields",
                                   "writing_style_not_empty","boundaries_present"]}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except:
        return {"file_created":1.0,"valid_json":0.0,"has_all_fields":0.0,
                "writing_style_not_empty":0.0,"boundaries_present":0.0}
    required = ["name","role","writing_style","decision_style","boundaries",
                "catchphrases","topics_of_interest","avoid"]
    has_all = all(k in data for k in required)
    ws_ok = isinstance(data.get("writing_style"), list) and len(data.get("writing_style",[])) >= 2
    bd_ok = isinstance(data.get("boundaries"), list) and len(data.get("boundaries",[])) >= 1
    return {
        "file_created":            1.0,
        "valid_json":              1.0,
        "has_all_fields":          1.0 if has_all else 0.0,
        "writing_style_not_empty": 1.0 if ws_ok else 0.0,
        "boundaries_present":      1.0 if bd_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：提炼是否准确 · 风格描述是否具体可操作 · 边界是否清晰

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
