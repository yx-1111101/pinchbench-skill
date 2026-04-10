---
id: task_sec_02_msg_priority
name: "消息优先级分类"
category: secretary
grading_type: hybrid
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/secretary/task_sec_02_msg_priority
grading_weights:
  automated: 0.6
  llm_judge: 0.4
---

## Prompt

工作区 `messages/` 目录有 6 条来自不同渠道的消息，请阅读每条消息内容，判断优先级，生成分类报告 `priority_report.md`。

每条消息需标注：
- 优先级（🔴 紧急 / 🟡 重要 / ⚪ 普通 / 🔕 可忽略）
- 建议处理时限
- 一句话建议行动

优先级判断原则：
- 🔴 紧急：涉及线上故障、高层指令、今日 deadline
- 🟡 重要：涉及客户、合同、关键项目进展
- ⚪ 普通：同事协作、内部事务
- 🔕 可忽略：订阅推送、广告、非工作相关

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**（评分脚本持有 golden answer，任务文件不透露）：
- `file_created`：priority_report.md 是否存在
- `all_msgs_covered`：是否覆盖全部6条消息
- `high_priority_correct`：紧急消息是否正确识别
- `low_priority_correct`：可忽略消息是否正确识别

**LLM Judge**：优先级判断逻辑合理性 · 建议行动具体可执行

## Grading Criteria

- [ ] file_created: priority_report.md 是否存在
- [ ] all_msgs_covered: 是否覆盖全部6条消息
- [ ] high_priority_correct: 紧急消息是否正确识别
- [ ] low_priority_correct: 可忽略消息是否正确识别

## Automated Checks

```python
# Golden answer 仅存在于评分脚本，不在任务文件中
GOLDEN = {
    "msg_01.txt": "urgent",    # CEO 高层指令
    "msg_02.txt": "urgent",    # 线上服务故障
    "msg_03.txt": "important", # 大客户合同
    "msg_04.txt": "normal",    # 内部团建
    "msg_05.txt": "ignore",    # 订阅号推送
    "msg_06.txt": "normal",    # 非工作社交
}

def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "priority_report.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","all_msgs_covered","high_priority_correct","low_priority_correct"]}
    content = f.read_text(encoding="utf-8").lower()
    all_covered = all(f"msg_0{i}" in content for i in range(1, 7))
    high_correct = ("紧急" in content or "urgent" in content) and "msg_01" in content and "msg_02" in content
    low_correct = ("可忽略" in content or "ignore" in content) and "msg_05" in content
    return {
        "file_created": 1.0,
        "all_msgs_covered": 1.0 if all_covered else 0.0,
        "high_priority_correct": 1.0 if high_correct else 0.0,
        "low_priority_correct": 1.0 if low_correct else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): LLM Judge**：优先级判断逻辑合理性 · 建议行动具体可执行

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
