"""接口层"""
from service import create_user, get_user


def handle_create_user(payload: dict) -> dict:
    username = payload.get("username", "")
    email = payload.get("email", "")
    if not username or not email:
        return {"error": "username and email required"}
    user = create_user(username=username, email=email)
    return {"user": user.to_dict()}


def handle_get_user(user_id: int) -> dict:
    try:
        user = get_user(user_id)
        return {"user": user.to_dict()}
    except KeyError as e:
        return {"error": str(e)}
