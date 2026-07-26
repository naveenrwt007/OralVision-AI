import asyncio

import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import MONGODB_URL


async def main():
    client = AsyncIOMotorClient(
        MONGODB_URL,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
    )

    try:
        result = await client.admin.command("ping")
        print("MongoDB connected successfully:", result)
    except Exception as error:
        print("MongoDB connection failed:")
        print(type(error).__name__)
        print(error)
    finally:
        client.close()


asyncio.run(main())