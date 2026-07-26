from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    TECHNICIAN = "technician"


class UserModel:
    def __init__(
        self,
        name: str,
        email: str,
        hashed_password: str,
        role: UserRole,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
    ):
        self.name = name
        self.email = email.lower().strip()
        self.hashed_password = hashed_password
        self.role = role
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }