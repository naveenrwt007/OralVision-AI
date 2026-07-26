from datetime import datetime, timezone

from app.core.database import users_collection
from app.core.security import hash_password


async def create_default_admin() -> None:
    email = "admin@oralvision.com"

    existing_user = await users_collection.find_one(
        {"email": email}
    )

    if existing_user:
        print("Default admin already exists.")
        return

    await users_collection.insert_one(
        {
            "name": "Administrator",
            "email": email,
            "hashed_password": hash_password("Admin@123"),
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
    )

    print("Default admin created successfully.")