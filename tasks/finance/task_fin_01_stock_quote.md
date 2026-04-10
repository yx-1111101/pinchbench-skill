---
id: task_fin_01_stock_quote
name: "实时行情数据获取与汇报"
category: finance
grading_type: automated
timeout_seconds: 120
workspace_files: []
dataset_dir: dataset/finance/task_fin_01_stock_quote
---

## Prompt

请查询以下三支股票的**今日**行情，并将结果保存到 `stock_report.txt`：

- 腾讯控股（00700.HK）
- 阿里巴巴（BABA）
- 英伟达（NVDA）

每支股票需包含：当前价格、今日涨跌幅、数据获取时间。

## Expected Behavior

The agent should complete the task as described in the prompt.

Evaluation criteria:
（对应 PinchBench task_02_stock 的 breakdown）

- `file_created`：stock_report.txt 存在
- `has_price_numbers`：文件中包含价格数字（含小数点）
- `has_change_info`：包含涨跌相关词（「%」「涨」「跌」「+」「-」）
- `mentions_all_tickers`：提到了全部三支股票代码或名称
- `has_timestamp`：包含时间信息（今日日期或具体时间）
- `well_formatted`：每支股票独立成段或成行（非一坨文字）

## Grading Criteria

- [ ] （对应 PinchBench task_02_stock 的 breakdown）
- [ ] file_created: stock_report.txt 存在
- [ ] has_price_numbers: 文件中包含价格数字（含小数点）
- [ ] has_change_info: 包含涨跌相关词（「%」「涨」「跌」「+」「-」）
- [ ] mentions_all_tickers: 提到了全部三支股票代码或名称
- [ ] has_timestamp: 包含时间信息（今日日期或具体时间）
- [ ] well_formatted: 每支股票独立成段或成行（非一坨文字）

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    f = workspace_path / "stock_report.txt"
    if not f.exists():
        return {k: 0.0 for k in ["file_created","has_price_numbers","has_change_info",
                                   "mentions_all_tickers","has_timestamp","well_formatted"]}
    content = f.read_text(encoding="utf-8")
    has_price = bool(re.search(r'\d+\.\d+', content))
    has_change = any(w in content for w in ["%","涨","跌","+","-","上涨","下跌"])
    mentions_all = all(t in content for t in ["腾讯","阿里","NVDA"]) or \
                   all(t in content for t in ["00700","BABA","NVDA"])
    has_time = bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}:\d{2}|今日|today', content, re.I))
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    well_fmt = len(lines) >= 3
    return {
        "file_created":       1.0,
        "has_price_numbers":  1.0 if has_price else 0.0,
        "has_change_info":    1.0 if has_change else 0.0,
        "mentions_all_tickers":1.0 if mentions_all else 0.0,
        "has_timestamp":      1.0 if has_time else 0.0,
        "well_formatted":     1.0 if well_fmt else 0.0,
    }
```
