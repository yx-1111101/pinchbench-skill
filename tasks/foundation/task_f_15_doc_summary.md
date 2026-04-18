---
id: task_f_15_doc_summary
name: "task_f_15_doc_summary"
category: foundation
grading_type: hybrid
timeout_seconds: 90
workspace_files:
  - summary_source.txt
dataset_dir: dataset/foundation/task_f_15_doc_summary
grading_weights:
  automated: 0.3
  llm_judge: 0.7
---

## Prompt

工作区提供一份输入文本 `summary_source.txt`（来自 `dataset/foundation/task_f_15_doc_summary/`）。请阅读后输出到 `summary_output.txt`，要求：

- **恰好 3 段**（用空行分隔）
- 第 1 段：主题与整体概述  
- 第 2 段：关键应用与收益（至少提到 2 个点）  
- 第 3 段：挑战/风险与未来展望

## Expected Behavior

The agent must summarize the **actual** English healthcare/AI article in `summary_source.txt`. Automated checks enforce three paragraphs and minimum length, and require that several topical anchors from the source domain appear in `summary_output.txt` (healthcare, imaging, privacy, etc.)—same “ground-truth keyword” idea as `task_f_02`. LLM judge still weighs fluency and accuracy.

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re

    f = workspace_path / "summary_output.txt"

    if not f.exists():
        return {
            "file_created": 0.0,
            "three_paragraphs": 0.0,
            "not_empty": 0.0,
            "source_keyword_hit_rate": 0.0,
        }

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]

    cl = content.lower()

    # Anchors from summary_source.txt (healthcare + AI themes)
    GROUPS = [
        ("healthcare", "医疗", "医学", "健康", "health"),
        ("artificial intelligence", "人工智能", "机器学习", "machine learning"),
        ("imag", "影像", "成像", "radiolog"),
        ("privacy", "隐私"),
        ("drug", "药物", "制药", "疫苗"),
    ]

    hits = sum(1 for syns in GROUPS if any(s in cl or s in content for s in syns))
    hit_rate = hits / len(GROUPS)

    return {
        "file_created": 1.0,
        "three_paragraphs": 1.0 if len(paras) == 3 else 0.0,
        "not_empty": 1.0 if len(content) >= 200 else 0.0,
        "source_keyword_hit_rate": round(hit_rate, 2),
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions (from task spec): 评价输出的准确性、结构清晰度和实用性

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
