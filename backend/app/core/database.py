from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.core.config import settings


class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    
db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on startup."""
    print(f"Connecting to MongoDB at {settings.MONGODB_URL}...")
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Test the connection
    try:
        await db.client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise e


async def close_mongo_connection():
    """Close MongoDB connection on shutdown."""
    print("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        print("✅ MongoDB connection closed.")


def get_database():
    """Get the database instance."""
    return db.client[settings.DATABASE_NAME]


# Collection getters for type hints and easy access
def get_users_collection():
    return get_database()["users"]


def get_memes_collection():
    return get_database()["memes"]


def get_transactions_collection():
    return get_database()["transactions"]
