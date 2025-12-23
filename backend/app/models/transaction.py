from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TransactionType(str, Enum):
    """Types of transactions."""
    BUY = "buy"
    SELL = "sell"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============ Transaction Models ============
class TransactionCreate(BaseModel):
    """Fields to create a transaction."""
    meme_id: str
    transaction_type: TransactionType
    quantity: int = Field(..., ge=1)
    # Optional seller-defined minimum price per share for post-IPO sell listings.
    limit_price: Optional[float] = Field(None, gt=0)


class TransactionInDB(BaseModel):
    """Transaction as stored in database."""
    id: str
    user_id: str
    username: str
    meme_id: str
    meme_ticker: str
    meme_name: str
    
    transaction_type: TransactionType
    quantity: int
    price_per_share: float  # Price at time of transaction
    total_value: float  # quantity * price_per_share
    
    status: TransactionStatus = TransactionStatus.COMPLETED
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionResponse(BaseModel):
    """Transaction response for API."""
    id: str
    meme_ticker: str
    meme_name: str
    transaction_type: str
    quantity: int
    price_per_share: float
    total_value: float
    status: str
    created_at: datetime


class TransactionHistory(BaseModel):
    """User's transaction history."""
    transactions: List[TransactionResponse]
    total: int
    page: int
    per_page: int


# ============ Engagement Actions ============
class EngagementType(str, Enum):
    """Types of engagement that affect price."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    COMMENT = "comment"
    REPORT = "report"
    SHARE = "share"


class EngagementAction(BaseModel):
    """Request to engage with a meme."""
    meme_id: str
    action: EngagementType
    comment_content: Optional[str] = None  # Only for COMMENT action


class EngagementResponse(BaseModel):
    """Response after engagement."""
    success: bool
    message: str
    new_price: float
    price_change: float
    price_change_percent: float
