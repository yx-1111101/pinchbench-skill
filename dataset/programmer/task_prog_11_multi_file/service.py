"""业务逻辑层"""
from models import User
from datetime import datetime

_user_store: dict = {}
_next_id: int = 1


def create_user(username: str, email: str) -> User:
    global _next_id
    user = User(
        id=_next_id,
        username=username,
        email=email,
        created_at=datetime.now().isoformat(),
    )
    _user_store[_next_id] = user
    _next_id += 1
    return user


def get_user(user_id: int) -> User:
    if user_id not in _user_store:
        raise KeyError(f"User {user_id} not found")
    return _user_store[user_id]
