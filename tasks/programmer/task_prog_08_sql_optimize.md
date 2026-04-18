---
id: task_prog_08_sql_optimize
name: "SQL 慢查询分析与优化"
category: programmer
grading_type: automated
timeout_seconds: 450
workspace_files:
  - slow_queries.sql
dataset_dir: dataset/programmer/task_prog_08_sql_optimize
---

## Prompt

工作区有一份慢查询报告 `slow_queries.sql`，包含3条在生产环境导致超时的 SQL，以及对应的 `EXPLAIN` 输出。

请：
1. 分析每条查询的性能瓶颈
2. 改写为高效版本，保存到 `optimized.sql`
3. 将分析说明写入 `sql_report.md`

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
- `file_created`：optimized.sql 存在
- `report_created`：sql_report.md 存在
- `q1_uses_index`：Q1 对应分段中包含索引相关改写（`INDEX`/`idx_`/避免函数包裹字段）
- `q2_avoids_subquery`：Q2 对应分段将相关子查询改为 JOIN
- `q3_adds_limit`：Q3 对应分段补充了 `LIMIT` 或分页控制
- `explains_bottleneck`：sql_report.md 包含性能瓶颈关键词（「全表扫描」/「子查询」/「索引」/「Full Scan」/「N+1」）

## Grading Criteria

- [ ] file_created: optimized.sql 存在
- [ ] report_created: sql_report.md 存在
- [ ] q1_uses_index: Q1 对应分段中包含索引相关改写（`INDEX`/`idx_`/避免函数包裹字段）
- [ ] q2_avoids_subquery: Q2 对应分段将相关子查询改为 JOIN
- [ ] q3_adds_limit: Q3 对应分段补充了 `LIMIT` 或分页控制
- [ ] explains_bottleneck: sql_report.md 包含性能瓶颈关键词（「全表扫描」/「子查询」/「索引」/「Full Scan」/「N+1」）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    opt = workspace_path / "optimized.sql"
    rpt = workspace_path / "sql_report.md"
    if not opt.exists():
        return {k: 0.0 for k in ["file_created","report_created","q1_uses_index",
                                   "q2_avoids_subquery","q3_adds_limit","explains_bottleneck"]}
    sql  = opt.read_text(encoding="utf-8")
    sql_upper = sql.upper()
    rpt_text = rpt.read_text(encoding="utf-8") if rpt.exists() else ""
    q1_section = re.search(r'(?:--\s*Q1|/\*\s*Q1\s*\*/)(.*?)(?=(?:--\s*Q2|/\*\s*Q2\s*\*/)|\Z)', sql_upper, re.DOTALL)
    q2_section = re.search(r'(?:--\s*Q2|/\*\s*Q2\s*\*/)(.*?)(?=(?:--\s*Q3|/\*\s*Q3\s*\*/)|\Z)', sql_upper, re.DOTALL)
    q3_section = re.search(r'(?:--\s*Q3|/\*\s*Q3\s*\*/)(.*?)(?=\Z)', sql_upper, re.DOTALL)
    q1_text = q1_section.group(1) if q1_section else ""
    q2_text = q2_section.group(1) if q2_section else ""
    q3_text = q3_section.group(1) if q3_section else ""
    q1_ok = bool(re.search(r'IDX_|INDEX|WHERE\s+\w+_DATE\b(?!\s*\()', q1_text))
    q2_ok = bool(re.search(r'\bJOIN\b', q2_text))
    q3_ok = bool(re.search(r'\bLIMIT\b|\bOFFSET\b|\bFETCH\b', q3_text))
    btl_kws = ["全表扫描","子查询","索引","full scan","n+1","nested","filesort","using where"]
    btl_ok  = any(k in rpt_text.lower() for k in btl_kws)
    return {
        "file_created":       1.0,
        "report_created":     1.0 if rpt.exists() else 0.0,
        "q1_uses_index":      1.0 if q1_ok else 0.0,
        "q2_avoids_subquery": 1.0 if q2_ok else 0.0,
        "q3_adds_limit":      1.0 if q3_ok else 0.0,
        "explains_bottleneck":1.0 if btl_ok else 0.0,
    }
```
