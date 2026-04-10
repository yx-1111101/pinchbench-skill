"""集成测试 - 验证 phone 字段变更后三层一致"""
import pytest
import service
import api


def setup_function():
    service._user_store.clear()
    service._next_id = 1


def test_create_user_with_phone():
    result = api.handle_create_user({
        "username": "alice",
        "email": "alice@example.com",
        "phone": "13800138000",
    })
    assert "user" in result
    assert result["user"]["phone"] == "13800138000"


def test_create_user_missing_phone_returns_error():
    result = api.handle_create_user({
        "username": "bob",
        "email": "bob@example.com",
    })
    assert "error" in result


def test_get_user_includes_phone():
    api.handle_create_user({
        "username": "carol",
        "email": "carol@example.com",
        "phone": "13900139000",
    })
    result = api.handle_get_user(1)
    assert result["user"]["phone"] == "13900139000"


def test_user_model_has_phone_field():
    from models import User
    import inspect
    fields = inspect.signature(User).parameters
    assert "phone" in fields
