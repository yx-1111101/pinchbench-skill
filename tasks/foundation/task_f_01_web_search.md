---
id: task_f_01_web_search
name: "task_f_01_web_search"
category: foundation
grading_type: automated
timeout_seconds: 180
workspace_files: []
dataset_dir: dataset/foundation/task_f_01_web_search
---

## Prompt

请搜索「英伟达（NVDA）今天的股票价格」，将结果保存到 `result.txt`。

## Expected Behavior

The agent should search for NVDA’s stock price and write results to `result.txt`. Automated grading checks that the file is non-empty, mentions NVIDIA / NVDA, contains a plausible price-like number, and (when a live reference close can be fetched) that a candidate price matches within tolerance—same spirit as other foundation tasks that tie scores to verifiable content.

Evaluation criteria:
- `file_created`：`result.txt` 是否存在  
- `file_not_empty`：文件原始内容是否非空（按写入字节判定，不因剔除噪声而判空）  
- `mentions_nvda`：是否出现 NVDA / 英伟达 等与标的股票一致的指称  
- `has_price_number`：剔除日期/时间噪声后，是否含股价形态的数值  
- `price_matches_live_close`：当参考收盘价拉取成功时，是否存在落在容差内的候选价；拉取失败时为 `0.0`（该项不可用）

## Grading Criteria

- [ ] file_created: `result.txt` 是否存在
- [ ] file_not_empty: 文件原始内容是否非空（按写入字节判定，不因剔除噪声而判空）
- [ ] mentions_nvda: 是否提及 NVDA / 英伟达
- [ ] has_price_number: 剔除日期/时间噪声后，是否含股价形态的数值
- [ ] price_matches_live_close: 参考价可用时价格是否在容差内，否则记 0

## Automated Checks

```python
def grade(transcript, workspace_path):
    from pathlib import Path
    workspace_path = Path(workspace_path)
    import re
    import urllib.request

    def strip_date_time_noise(s):
        if not s:
            return ""
        t = s
        t = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", t)
        t = re.sub(r"\b\d{4}/\d{1,2}/\d{1,2}\b", " ", t)
        t = re.sub(r"\d{4}年\d{1,2}月\d{1,2}日", " ", t)
        t = re.sub(r"\d{1,2}月\d{1,2}日", " ", t)
        t = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", t)
        return t

    def fetch_nvda_close():
        url = "https://stooq.com/q/l/?s=nvda.us&f=sd2t2ohlcv&h&e=csv"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "OpenFridayBench/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                text = r.read().decode("utf-8", errors="ignore")
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            if len(lines) < 2:
                return None
            parts = lines[1].split(",")
            if len(parts) < 7:
                return None
            return float(parts[6])
        except Exception:
            return None

    def extract_candidate_prices(content):
        out = []
        for m in re.finditer(
            r"\$\s*(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})\b", content
        ):
            try:
                whole = m.group(1).replace(",", "")
                out.append(float(f"{whole}.{m.group(2)}"))
            except ValueError:
                pass
        for m in re.finditer(
            r"(?<![\d.])(\d{1,3}(?:,\d{3})*|\d+)\.(\d{2})(?!\d)", content
        ):
            try:
                whole = m.group(1).replace(",", "")
                v = float(f"{whole}.{m.group(2)}")
                if 5.0 <= v <= 6000.0:
                    out.append(v)
            except ValueError:
                pass
        for m in re.finditer(r"\b(\d{3,4})\b", content):
            v = int(m.group(1))
            if 100 <= v <= 999 or 1000 <= v <= 5999:
                out.append(float(v))
        return out

    f = workspace_path / "result.txt"
    exists = f.exists()
    raw = f.read_text(encoding="utf-8", errors="ignore").strip() if exists else ""
    raw_lower = raw.lower()
    content = strip_date_time_noise(raw)

    price_like = re.compile(
        r"(?:\$\s*)?\d{1,3}(?:,\d{3})+\.\d{2}|\d{1,4}\.\d{2}|\b(?:[1-9]\d{2}|[1-5]\d{3})\b"
    )
    has_price_number = bool(price_like.search(content))

    mentions_nvda = ("nvda" in raw_lower) or ("英伟达" in raw) or ("nvidia" in raw_lower)

    scores = {
        "file_created": 1.0 if exists else 0.0,
        "file_not_empty": 1.0 if len(raw) > 0 else 0.0,
        "mentions_nvda": 1.0 if mentions_nvda else 0.0,
        "has_price_number": 1.0 if has_price_number else 0.0,
        "price_matches_live_close": 0.0,
    }

    ref = fetch_nvda_close()
    if ref is not None:
        candidates = extract_candidate_prices(content)
        tol = max(ref * 0.04, 2.0)
        ok = any(abs(c - ref) <= tol for c in candidates)
        scores["price_matches_live_close"] = 1.0 if ok else 0.0

    return scores
```
