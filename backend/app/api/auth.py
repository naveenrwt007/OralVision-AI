from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_current_admin,
    get_current_user,
    public_user,
)
from app.schemas.auth import LoginRequest, UserCreate
from app.services.auth_service import login_user, register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    current_admin: dict[str, Any] = Depends(
        get_current_admin
    ),
):
    created = await register_user(
        user.name,
        user.email,
        user.password,
        user.role.value,
    )

    if created is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return {
        "message": "User registered successfully",
        "user": {
            "id": str(created["_id"]),
            "name": created["name"],
            "email": created["email"],
            "role": created["role"],
            "is_active": created["is_active"],
            "created_at": created.get("created_at"),
        },
        "created_by": {
            "id": str(current_admin["_id"]),
            "name": current_admin["name"],
            "email": current_admin["email"],
            "role": current_admin["role"],
        },
    }


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
)
async def signup(user: UserCreate):
    if user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration cannot create an administrator account",
        )

    created = await register_user(
        user.name,
        user.email,
        user.password,
        user.role.value,
    )

    if created is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    return {
        "message": "Registration successful",
        "user": {
            "id": str(created["_id"]),
            "name": created["name"],
            "email": created["email"],
            "role": created["role"],
            "is_active": created["is_active"],
            "created_at": created.get("created_at"),
        },
    }


@router.post("/login")
async def login(request: LoginRequest):
    result = await login_user(
        request.email,
        request.password,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result


@router.get("/me")
async def get_my_profile(
    current_user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    return {
        "user": public_user(current_user)
    }