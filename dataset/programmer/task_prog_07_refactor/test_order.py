import pytest
from order_processor import process_order, FakeDB


def setup_function():
    FakeDB.orders.clear()
    FakeDB.inventory = {"SKU-001": 100, "SKU-002": 50, "SKU-003": 0}


def make_order(**kwargs):
    base = {
        "order_id": "ORD-001",
        "user_email": "test@example.com",
        "items": [{"sku": "SKU-001", "qty": 1}],
        "shipping_address": "上海市浦东新区",
    }
    base.update(kwargs)
    return base


def test_valid_order_returns_ok():
    r = process_order(make_order())
    assert r["status"] == "ok"
    assert r["order"]["total"] == 119.0   # 99 + 20 shipping


def test_free_shipping_over_500():
    r = process_order(make_order(items=[{"sku": "SKU-001", "qty": 6}]))
    assert r["order"]["shipping_fee"] == 0.0


def test_coupon_save10():
    r = process_order(make_order(coupon="SAVE10"))
    assert r["order"]["discount"] == pytest.approx(9.9)


def test_missing_field_returns_error():
    r = process_order({"order_id": "X", "items": []})
    assert r["status"] == "error"


def test_invalid_email_returns_error():
    r = process_order(make_order(user_email="not-an-email"))
    assert r["status"] == "error"


def test_out_of_stock_returns_error():
    r = process_order(make_order(items=[{"sku": "SKU-003", "qty": 1}]))
    assert r["status"] == "error"
    assert "stock" in r["message"].lower()


def test_stock_deducted_after_order():
    process_order(make_order(items=[{"sku": "SKU-001", "qty": 3}]))
    assert FakeDB.inventory["SKU-001"] == 97


def test_order_saved_to_db():
    process_order(make_order())
    assert len(FakeDB.orders) == 1
