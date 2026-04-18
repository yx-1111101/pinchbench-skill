---
id: task_prog_03_code_review
name: "代码 Diff 审查 → 专业 Code Review 意见"
category: programmer
grading_type: hybrid
timeout_seconds: 150
workspace_files:
  - changes.diff
dataset_dir: dataset/programmer/task_prog_03_code_review
grading_weights:
  automated: 0.4
  llm_judge: 0.6
---

## Prompt

工作区有一份 Git diff 文件 `changes.diff`，是同事提交的一个用户行为数据分析脚本的 PR（基于 pandas + SQLite）。

请以 Senior Data Engineer 身份做 Code Review，将审查意见保存到 `review.md`，要求：

- 指出**正确性 / 数据问题**（最高优先级）
- 指出**性能问题**（可选修改，但需说明影响）
- 指出**代码风格 / 可维护性**问题
- 每条意见需注明：所在位置、问题描述、修改建议
- 最后给出整体评价：**Approve / Request Changes / Comment**

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
**自动**（基于 diff 中预埋的已知问题）：

- `file_created`：review.md 存在
- `sql_injection_found`：识别出 SQL 拼接注入风险（「注入」「injection」「参数化」「parameterize」「f-string」「format」）
- `iterrows_perf_found`：识别出 iterrows 性能问题（「iterrows」「vectorize」「向量化」「性能」「apply」）
- `has_verdict`：包含最终评价（「Approve」「Request Changes」「建议修改」「阻断」「LGTM」）
- `has_code_reference`：引用了具体代码片段或行号

**LLM Judge**：SQL 注入分析是否准确给出修复示例 · 性能建议是否量化 · Review 整体专业度

## Grading Criteria

- [ ] file_created: review.md 存在
- [ ] sql_injection_found: 识别出 SQL 拼接注入风险（「注入」「injection」「参数化」「parameterize」「f-string」「format」）
- [ ] iterrows_perf_found: 识别出 iterrows 性能问题（「iterrows」「vectorize」「向量化」「性能」「apply」）
- [ ] has_verdict: 包含最终评价（「Approve」「Request Changes」「建议修改」「阻断」「LGTM」）
- [ ] has_code_reference: 引用了具体代码片段或行号

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "review.md"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","sql_injection_found",
                                   "iterrows_perf_found","has_verdict","has_code_reference"]}
    content = f.read_text(encoding="utf-8")
    sql_kws     = ["注入","injection","参数化","parameterize","parameterized",
                   "f-string","f\"","f'","format","?","placeholder","绑定参数"]
    iter_kws    = ["iterrows","vectorize","向量化","性能","apply","矢量","慢","O(n)"]
    verdict_kws = ["Approve","Request Changes","建议修改","阻断","不能合并","LGTM","changes requested"]
    cl = content.lower()
    sql_ok = any(kw.lower() in cl for kw in sql_kws)
    iter_ok = any(kw.lower() in cl for kw in iter_kws)
    verdict_ok = any(kw.lower() in cl for kw in verdict_kws)
    triple_ticks = "`" * 3
    ref_ok = bool(re.search(r'第\s*\d+\s*行|line\s*\d+|L\d+|`[^`]+`', content, re.I)) or (triple_ticks in content)
    return {
        "file_created":         1.0,
        "sql_injection_found":  1.0 if sql_ok else 0.0,
        "iterrows_perf_found":  1.0 if iter_ok else 0.0,
        "has_verdict":          1.0 if verdict_ok else 0.0,
        "has_code_reference":   1.0 if ref_ok else 0.0,
    }
```

## LLM Judge Rubric

### Quality Assessment

Evaluate the agent's output against the task requirements.

Dimensions: SQL 注入分析是否准确给出修复示例 · 性能建议是否量化 · Review 整体专业度SQL 注入分析是否准确给出修复示例 · 性能建议是否量化 · Review 整体专业度

**Score 1.0**: Fully meets all requirements with high quality
**Score 0.75**: Meets most requirements with minor gaps
**Score 0.5**: Partially meets requirements
**Score 0.25**: Significant gaps or quality issues
**Score 0.0**: Does not address the task
