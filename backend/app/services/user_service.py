from datetime import datetime
from typing import Optional
from bson import ObjectId

from app.core.database import get_users_collection
from app.core.security import get_password_hash, verify_password
from app.models.user import UserCreate, UserInDB, UserResponse


async def get_user_by_email(email: str) -> Optional[dict]:
    """
    Find a user by their email address.
    
    Returns the raw MongoDB document or None.
    """
    users = get_users_collection()
    user = await users.find_one({"email": email.lower()})
    return user


async def get_user_by_username(username: str) -> Optional[dict]:
    """
    Find a user by their username.
    
    Returns the raw MongoDB document or None.
    """
    users = get_users_collection()
    user = await users.find_one({"username": username.lower()})
    return user


async def get_user_by_id(user_id: str) -> Optional[dict]:
    """
    Find a user by their ID.
    
    Returns the raw MongoDB document or None.
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        return None
        
    user = await users.find_one({"_id": ObjectId(user_id)})
    return user


async def create_user(user_data: UserCreate) -> dict:
    """
    Create a new user in the database.
    
    This is where we:
    1. Hash the password (NEVER store plain text!)
    2. Set default values (100 coins, 0 street cred)
    3. Insert into MongoDB
    4. Return the created user
    """
    users = get_users_collection()
    
    # Create the user document
    user_doc = {
        "username": user_data.username.lower(),
        "email": user_data.email.lower(),
        "hashed_password": get_password_hash(user_data.password),  # 🔐 HASH THE PASSWORD!
        "wallet_balance": 10000.0,  # Starting balance
        "street_cred": 0,
        "portfolio": [],
        "total_trades": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # Insert into MongoDB
    result = await users.insert_one(user_doc)
    
    # Get the created user
    created_user = await users.find_one({"_id": result.inserted_id})
    return created_user


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with email and password.
    
    This is the core authentication logic:
    1. Find user by email
    2. If not found -> return None (user doesn't exist)
    3. Verify password using bcrypt
    4. If password wrong -> return None
    5. If password correct -> return user
    
    The verify_password function compares:
    - The plain password the user just entered
    - The hashed password stored in database
    
    It does NOT decrypt the hash (that's impossible with bcrypt).
    Instead, it hashes the input password with the same salt
    and compares the two hashes.
    """
    # Step 1: Find the user
    user = await get_user_by_email(email)
    
    if not user:
        # User doesn't exist
        return None
    
    # Step 2: Verify password
    # This compares plain password with hashed password in DB
    if not verify_password(password, user["hashed_password"]):
        # Wrong password!
        return None
    
    # Step 3: Password correct, return user
    return user


def user_doc_to_response(user_doc: dict) -> UserResponse:
    """
    Convert MongoDB document to UserResponse (safe for client).
    
    This removes sensitive data like hashed_password.
    """
    return UserResponse(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        email=user_doc["email"],
        wallet_balance=user_doc["wallet_balance"],
        street_cred=user_doc["street_cred"],
        portfolio=user_doc.get("portfolio", []),
        created_at=user_doc["created_at"],
    )


async def update_user_wallet(user_id: str, new_balance: float) -> bool:
    """Update user's wallet balance."""
    users = get_users_collection()
    
    result = await users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "wallet_balance": new_balance,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return result.modified_count > 0
