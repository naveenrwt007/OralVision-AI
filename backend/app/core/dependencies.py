from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import users_collection
from app.core.security import decode_access_token


bearer_scheme = HTTPBearer(
    scheme_name="JWT Bearer",
    description="Enter the JWT token returned by /auth/login",
    auto_error=True,
)


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "is_active": user.get("is_active", True),
        "created_at": user.get("created_at"),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme
    ),
) -> dict[str, Any]:
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await users_collection.find_one(
        {"email": email.lower().strip()}
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


def require_roles(*allowed_roles: str) -> Callable:
    async def role_checker(
        current_user: dict[str, Any] = Depends(
            get_current_user
        ),
    ) -> dict[str, Any]:

        role = current_user.get("role", "").lower()

        if role not in [r.lower() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return role_checker


async def get_current_admin(
    current_user: dict[str, Any] = Depends(
        require_roles("admin")
    ),
) -> dict[str, Any]:
    return current_user


async def get_current_doctor(
    current_user: dict[str, Any] = Depends(
        require_roles("admin", "doctor")
    ),
) -> dict[str, Any]:
    return current_user


async def get_current_technician(
    current_user: dict[str, Any] = Depends(
        require_roles(
            "admin",
            "doctor",
            "technician",
        )
    ),
) -> dict[str, Any]:
    return current_user