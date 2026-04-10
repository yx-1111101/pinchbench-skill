"""
订单处理模块 - process_order 是一个需要重构的上帝函数
"""
import re
from datetime import datetime


# 模拟数据库和邮件发送（不需要真实依赖）
class FakeDB:
    orders = []
    inventory = {"SKU-001": 100, "SKU-002": 50, "SKU-003": 0}

    @classmethod
    def save_order(cls, order): cls.orders.append(order)

    @classmethod
    def get_stock(cls, sku): return cls.inventory.get(sku, 0)

    @classmethod
    def deduct_stock(cls, sku, qty): cls.inventory[sku] = max(0, cls.inventory.get(sku, 0) - qty)


def send_email(to, subject, body): pass  # stub


def process_order(order_dict: dict) -> dict:
    """处理订单 - 当前实现为上帝函数，需重构"""
    # ── 1. 基础字段校验 ──────────────────────────────────────
    required = ["order_id", "user_email", "items", "shipping_address"]
    for field in required:
        if field not in order_dict:
            return {"status": "error", "message": f"Missing field: {field}"}

    if not re.match(r"[^@]+@[^@]+\.[^@]+", order_dict["user_email"]):
        return {"status": "error", "message": "Invalid email"}

    if not order_dict["items"]:
        return {"status": "error", "message": "Order has no items"}

    # ── 2. 库存检查 ───────────────────────────────────────────
    for item in order_dict["items"]:
        if "sku" not in item or "qty" not in item:
            return {"status": "error", "message": f"Item missing sku or qty"}
        stock = FakeDB.get_stock(item["sku"])
        if stock < item["qty"]:
            return {"status": "error", "message": f"Insufficient stock for {item['sku']}"}

    # ── 3. 价格计算 ───────────────────────────────────────────
    PRICE_TABLE = {"SKU-001": 99.0, "SKU-002": 199.0, "SKU-003": 49.0}
    subtotal = 0.0
    for item in order_dict["items"]:
        price = PRICE_TABLE.get(item["sku"], 0.0)
        subtotal += price * item["qty"]

    # 运费逻辑
    if subtotal >= 500:
        shipping_fee = 0.0
    elif subtotal >= 200:
        shipping_fee = 10.0
    else:
        shipping_fee = 20.0

    # 折扣逻辑
    discount = 0.0
    if order_dict.get("coupon") == "SAVE10":
        discount = subtotal * 0.10
    elif order_dict.get("coupon") == "SAVE20":
        discount = subtotal * 0.20

    total = round(subtotal + shipping_fee - discount, 2)

    # ── 4. 扣库存 ─────────────────────────────────────────────
    for item in order_dict["items"]:
        FakeDB.deduct_stock(item["sku"], item["qty"])

    # ── 5. 写订单记录 ─────────────────────────────────────────
    order_record = {
        "order_id": order_dict["order_id"],
        "user_email": order_dict["user_email"],
        "items": order_dict["items"],
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount": discount,
        "total": total,
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
        "shipping_address": order_dict["shipping_address"],
    }
    FakeDB.save_order(order_record)

    # ── 6. 发确认邮件 ─────────────────────────────────────────
    subject = f"Order {order_dict['order_id']} Confirmed"
    body = (
        f"Hi,\n\nYour order {order_dict['order_id']} has been confirmed.\n"
        f"Total: ¥{total}\nShipping to: {order_dict['shipping_address']}\n\nThanks!"
    )
    send_email(order_dict["user_email"], subject, body)

    return {"status": "ok", "order": order_record}
