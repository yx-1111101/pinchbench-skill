---
id: task_f_05_pdf_parse
name: "task_f_05_pdf_parse"
category: foundation
grading_type: automated
timeout_seconds: 60
workspace_files:
  - report.pdf
dataset_dir: dataset/foundation/task_f_05_pdf_parse
---

## Prompt

工作区有一个 PDF 文件 `report.pdf`，内容是一份产品报告。

请提取 PDF 全文，保存为 `extracted.txt`。

## Expected Behavior

The agent should extract the real text from `report.pdf` into `extracted.txt`. Automated grading checks that several phrases that appear in the PDF (`report.pdf`) are present in the extraction, so random filler text does not pass.

Evaluation criteria:
- `file_created`: extracted.txt 是否存在
- `keyword_hit_rate`: 命中 PDF 金标短语组的比例（0–1）

## Grading Criteria

- [ ] file_created: extracted.txt 是否存在
- [ ] keyword_hit_rate: 金标短语组命中率（与 `report.pdf` 正文一致）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    f = workspace_path / "extracted.txt"
    if not f.exists():
        return {"file_created": 0.0, "keyword_hit_rate": 0.0}

    content = f.read_text(encoding="utf-8", errors="ignore").strip()
    c_lower = content.lower()

    # Strings from the actual PDF text in dataset/foundation/task_f_05_pdf_parse/report.pdf
    GROUND_TRUTH_KEYWORDS = [
        ("product report", "document type: product report"),
        ("smartdesk ai assistant", "smartdesk"),
        ("2026-03-11", "2026/03/11"),
        ("core features", "meeting summary", "deadline reminders"),
        ("risks and challenges", "privacy compliance", "hallucination"),
    ]

    hits = sum(
        1 for synonyms in GROUND_TRUTH_KEYWORDS
        if any(s in c_lower for s in synonyms)
    )
    hit_rate = hits / len(GROUND_TRUTH_KEYWORDS)

    return {
        "file_created": 1.0,
        "keyword_hit_rate": round(hit_rate, 2),
    }
```
