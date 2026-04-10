import csv
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


def load_records(filepath: str, encoding: str = "utf-8") -> List[Dict]:
    records = []
    with open(filepath, encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(dict(row))
    return records


def filter_by_date(records: List[Dict], field: str, start: str, end: str) -> List[Dict]:
    fmt = "%Y-%m-%d"
    start_dt = datetime.strptime(start, fmt)
    end_dt = datetime.strptime(end, fmt)
    result = []
    for r in records:
        try:
            dt = datetime.strptime(r[field], fmt)
            if start_dt <= dt <= end_dt:
                result.append(r)
        except (KeyError, ValueError):
            continue
    return result


def aggregate(records: List[Dict], group_by: str, value_field: str) -> Dict[str, float]:
    totals: Dict[str, float] = {}
    for r in records:
        key = r.get(group_by, "unknown")
        try:
            val = float(r.get(value_field, 0))
        except (TypeError, ValueError):
            val = 0.0
        totals[key] = totals.get(key, 0.0) + val
    return totals


def normalize(data: Dict[str, float]) -> Dict[str, float]:
    if not data:
        return {}
    total = sum(data.values())
    if total == 0:
        return {k: 0.0 for k in data}
    return {k: round(v / total, 4) for k, v in data.items()}


def export_json(data: Any, filepath: str, indent: int = 2) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
