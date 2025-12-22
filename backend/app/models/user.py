from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


class PyObjectId(str):
    """Custom type for MongoDB ObjectId."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError("Invalid ObjectId")


# ============ Portfolio Item ============
class PortfolioItem(BaseModel):
    """A single meme holding in user's portfolio."""
    meme_id: str
    quantity_owned: int = 0
    average_buy_price: float = 0.0
    total_investment_value: float = 0.0


# ============ User Models ============
class UserBase(BaseModel):
    """Base user fields."""
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr


class UserCreate(UserBase):
    """Fields required to create a new user."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Fields required to login."""
    email: EmailStr
    password: str


class UserInDB(UserBase):
    """User as stored in database (with hashed password)."""
    id: Optional[str] = Field(None, alias="_id")
    hashed_password: str
    wallet_balance: float = 100.0  # Starting balance
    street_cred: int = 0
    portfolio: List[PortfolioItem] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserResponse(UserBase):
    """User data returned to client (no password!)."""
    id: str
    wallet_balance: float
    street_cred: int
    portfolio: List[PortfolioItem] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Fields that can be updated."""
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    email: Optional[EmailStr] = None


# ============ Auth Response Models ============
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT."""
    user_id: Optional[str] = None


class LoginResponse(BaseModel):
    """Response after successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SignupResponse(BaseModel):
    """Response after successful signup."""
    message: str
    user: UserResponse
