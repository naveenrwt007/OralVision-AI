from datetime import datetime

from app.core.database import users_collection
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


async def register_user(name, email, password, role):

    email = email.lower().strip()

    existing = await users_collection.find_one(
        {"email": email}
    )

    if existing:
        return None

    user = {
        "name": name,
        "email": email,
        "hashed_password": hash_password(password),
        "role": role,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }

    result = await users_collection.insert_one(user)

    user["_id"] = str(result.inserted_id)

    return user


async def authenticate_user(email, password):

    email = email.lower().strip()

    user = await users_collection.find_one(
        {"email": email}
    )

    if not user:
        return None

    if not verify_password(
        password,
        user["hashed_password"],
    ):
        return None

    return user


async def login_user(email, password):

    user = await authenticate_user(
        email,
        password,
    )

    if not user:
        return None

    token = create_access_token(
        {
            "sub": user["email"],
            "role": user["role"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 28800,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
        },
    }