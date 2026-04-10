"""
销售数据清洗脚本 - 每日凌晨批量清洗当日销售记录
用法: python clean_sales.py [--test]
"""
import sys
import pandas as pd

RAW_DATA = [
    {"order_id": "A001", "region": "华东", "amount": "299.0",  "qty": "2", "status": "completed"},
    {"order_id": "A002", "region": "华南", "amount": "150.0",  "qty": None, "status": "completed"},
    {"order_id": "A003", "region": "华东", "amount": "88.5",   "qty": "1", "status": "completed"},
    {"order_id": "A004", "region": "华北", "amount": None,     "qty": "3", "status": "completed"},
    {"order_id": "A005", "region": "华东", "amount": "420.0",  "qty": "1", "status": "refunded"},
    {"order_id": "A006", "region": "华东", "amount": "199.0",  "qty": "2", "status": "completed"},
    {"order_id": "A007", "region": "华南", "amount": "512.0",  "qty": "1", "status": "completed"},
    {"order_id": "A008", "region": "华北", "amount": "482.0",  "qty": "4", "status": "completed"},
]


def load_data():
    df = pd.DataFrame(RAW_DATA)
    return df


def clean(df):
    # 只保留 completed 状态
    df = df[df["status"] == "completed"]

    # BUG 1: amount 列是字符串，直接 astype(float) 会对 None 值抛 ValueError
    # 正确做法: pd.to_numeric(df["amount"], errors="coerce")
    df["amount"] = df["amount"].astype(float)

    # BUG 2: qty 列同样有 None，且转 int 前未处理 NaN，会抛 ValueError/TypeError
    # 正确做法: 先 coerce 转 float，fillna 后再转 int
    df["qty"] = df["qty"].astype(int)

    # BUG 3: 链式赋值 (SettingWithCopyWarning)，对筛选后的 df 子集写入 discount 列
    # 实际上写回的是临时副本，不会影响原 df，导致 discount 列始终为 NaN
    # 正确做法: 使用 df.loc[:, "discount"] = ... 或在 copy() 上操作
    df[df["amount"] > 400]["discount"] = 0.1

    return df


def summarize(df):
    revenue = round(df["amount"].sum(), 2)
    top_region = df.groupby("region")["amount"].sum().idxmax()
    return len(df), revenue, top_region


def main(test_mode=False):
    df = load_data()
    df = clean(df)
    valid_rows, revenue, top_region = summarize(df)

    if test_mode:
        print(f"valid_rows: {valid_rows}")
        print(f"revenue: {revenue}")
        print(f"top_region: {top_region}")
    else:
        print({"valid_rows": valid_rows, "revenue": revenue, "top_region": top_region})


if __name__ == "__main__":
    main(test_mode="--test" in sys.argv)
