---
id: task_twin_08_speak_as_me
name: "调用执行 — 给会议背景，生成用户风格的发言稿"
category: digital_twin
grading_type: hybrid
timeout_seconds: 450
workspace_files:
  - style_guide.md
  - meeting_brief.txt
dataset_dir: dataset/digital_twin/task_twin_08_speak_as_me
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

工作区有陈默的风格指南 `style_guide.md` 和会议背景文件 `meeting_brief.txt`。

**会议背景**：Q2 产品规划对齐会，陈默需发言10分钟，说明为什么 Q2 要砍掉3个功能需求，集中资源做核心链路优化。参与者：产品团队10人、研发负责人、业务VP。

请生成发言稿 `speech_draft.md`，要求：
- 约10分钟口播（1000-2000字）
- 符合陈默「数据说话、直接、不绕弯」风格
- 有具体数据支撑（可用合理假设数据）
- 结尾有清晰行动号召

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**：
- `file_created`：speech_draft.md 存在
- `length_ok`：字数在 1000-2000 字之间
- `has_data`：包含数字或百分比
- `has_conclusion`：结尾明确提出行动号召（如请团队确认、推进、执行、反馈）

**LLM Judge**：是否符合风格规则 · 论证是否有说服力 · 节奏是否适合口播

## Grading Criteria

- [ ] file_created: speech_draft.md 存在
- [ ] length_ok: 字数在 1000-2000 字之间
- [ ] has_data: 包含数字或百分比
- [ ] has_conclusion: 结尾明确提出行动号召（如请团队确认、推进、执行、反馈）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "speech_draft.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","length_ok","has_data","has_conclusion"]}
    content = f.read_text(encoding="utf-8").strip()
    char_count = len(content.replace(" ","").replace("\n",""))
    has_data   = bool(re.search(r'\d+[%％万亿]|\d+\.\d+', content))
    has_end    = any(w in content[-300:] for w in ["请大家","请团队","请各位","本周内","今天","下周","推进","执行","确认","反馈","对齐"])
    return {
        "file_created":  1.0,
        "length_ok":     1.0 if 1000 <= char_count <= 2000 else 0.0,
        "has_data":      1.0 if has_data else 0.0,
        "has_conclusion":1.0 if has_end else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: 是否符合风格规则 · 论证是否有说服力 · 节奏是否适合口播

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
