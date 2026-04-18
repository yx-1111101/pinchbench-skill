---
id: task_f_10_file_rw
name: "task_f_10_file_rw"
category: foundation
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/foundation/task_f_10_file_rw
---

## Prompt

请完成以下三步文件操作：

1. 创建文件 `note.txt`，写入内容：「第一次写入」
2. 读取 `note.txt` 的内容，确认读取成功
3. 在 `note.txt` 末尾追加内容：「第二次追加」
4. 将最终文件内容写入 `result.txt`

## Expected Behavior

The agent should perform real read/write/append so `result.txt` reflects the final `note.txt` contents. Grading checks that both required phrases appear and that **「第一次写入」 appears before 「第二次追加」** in `result.txt` (order correctness), and also inspects transcript trajectory evidence to reduce credit for answer-only shortcuts.

Evaluation criteria:
- `note_created`: note.txt 是否存在
- `result_created`: result.txt 是否存在
- `has_first_write`: result.txt 是否包含「第一次写入」
- `has_append`: result.txt 是否包含「第二次追加」
- `order_correct`: 「第一次写入」是否出现在「第二次追加」之前
- `trajectory_evidence_rate`: 执行轨迹中“创建/读取/追加/写结果”证据命中比例（0–1）

## Grading Criteria

- [ ] note_created: note.txt 是否存在
- [ ] result_created: result.txt 是否存在
- [ ] has_first_write: result.txt 是否包含「第一次写入」
- [ ] has_append: result.txt 是否包含「第二次追加」
- [ ] order_correct: 两段文字顺序是否正确
- [ ] trajectory_evidence_rate: 轨迹证据命中率（创建/读取/追加/写结果）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    import json
    workspace_path = Path(workspace_path)
    note = workspace_path / "note.txt"
    result = workspace_path / "result.txt"
    if not result.exists():
        return {
            "note_created": 1.0 if note.exists() else 0.0,
            "result_created": 0.0,
            "has_first_write": 0.0,
            "has_append": 0.0,
            "order_correct": 0.0,
            "trajectory_evidence_rate": 0.0,
        }
    c = result.read_text(encoding="utf-8", errors="ignore")
    a, b = "第一次写入", "第二次追加"
    i1, i2 = c.find(a), c.find(b)
    order_ok = i1 != -1 and i2 != -1 and i1 < i2

    # Trajectory evidence from execution transcript.
    # We expect process signals for create/read/append/write-result actions.
    def flatten_transcript(x):
        if x is None:
            return ""
        if isinstance(x, str):
            return x
        try:
            return json.dumps(x, ensure_ascii=False)
        except Exception:
            return str(x)

    t = flatten_transcript(transcript)
    tl = t.lower()
    TRACE_GROUPS = [
        ("note.txt", "创建", "create"),
        ("读取", "read", "cat", "open"),
        ("追加", "append", ">>"),
        ("result.txt", "写入", "write", "copy", "cp"),
    ]
    trace_hits = sum(
        1
        for syns in TRACE_GROUPS
        if any((s in t) or (s in tl) for s in syns)
    )
    trajectory_evidence_rate = trace_hits / len(TRACE_GROUPS)

    return {
        "note_created": 1.0 if note.exists() else 0.0,
        "result_created": 1.0,
        "has_first_write": 1.0 if a in c else 0.0,
        "has_append": 1.0 if b in c else 0.0,
        "order_correct": 1.0 if order_ok else 0.0,
        "trajectory_evidence_rate": round(trajectory_evidence_rate, 2),
    }
```
