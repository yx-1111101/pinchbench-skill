"""用户数据模型"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: str = ""

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
        }
