import certifi
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import DATABASE_NAME, MONGODB_URL


client = AsyncIOMotorClient(
    MONGODB_URL,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
)

database = client[DATABASE_NAME]

patients_collection = database["patients"]
screenings_collection = database["screenings"]
reports_collection = database["reports"]
users_collection = database["users"]


async def check_database_connection() -> bool:
    try:
        await client.admin.command("ping")
        return True
    except Exception as error:
        print(f"MongoDB connection error: {error}")
        return False