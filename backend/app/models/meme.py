from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============ Enums ============
class MemeCategory(str, Enum):
    """Categories for memes."""
    CRYPTO = "crypto"
    STONKS = "stonks"
    WOJAK = "wojak"
    PEPE = "pepe"
    ANIME = "anime"
    GAMING = "gaming"
    POLITICS = "politics"
    SPORTS = "sports"
    TECH = "tech"
    OTHER = "other"


class TrendStatus(str, Enum):
    """Meme trend status."""
    HOT = "hot"  # Rapidly rising                                                                                                                                                                                                                                                                                                                                                                   
    STABLE = "stable"  # Steady price
    COLD = "cold"  # Declining
    VOLATILE = "volatile"  # Big swings


# ============ Comment Model ============
class CommentBase(BaseModel):
    """Base comment fields."""
    content: str = Field(..., min_length=1, max_length=500)


class CommentCreate(CommentBase):
    """Fields to create a comment."""
    pass


class Comment(CommentBase):
    """Full comment with metadata."""
    id: str
    user_id: str
    username: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = 0


# ============ Meme Models ============
class MemeBase(BaseModel):
    """Base meme fields."""
    name: str = Field(..., min_length=1, max_length=100)
    ticker: str = Field(..., min_length=1, max_length=10)  # Like $DOGE, $PEPE
    description: str = Field(..., max_length=500)
    image_url: str
    category: MemeCategory = MemeCategory.OTHER


class MemeCreate(MemeBase):
    """Fields to create a new meme."""
    initial_price: float = Field(default=10.0, ge=0.01)
    total_shares: int = Field(default=1000000, ge=1000)
    ipo_percent: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    ipo_duration_minutes: Optional[int] = Field(default=None, ge=1, le=7 * 24 * 60)


class MemeInDB(MemeBase):
    """Meme as stored in database."""
    id: str
    creator_id: str
    creator_username: str
    
    # Price & Market data
    current_price: float = 10.0
    previous_price: float = 10.0
    price_change_24h: float = 0.0
    price_change_percent_24h: float = 0.0
    all_time_high: float = 10.0
    all_time_low: float = 10.0
    
    # Supply & Trading
    total_shares: int = 1000000
    available_shares: int = 1000000  # Shares available to buy

    # IPO (primary offering) - fixed-price pool sold by the system
    ipo_price: float = 10.0
    ipo_percent: float = 0.20
    ipo_duration_minutes: int = 60
    ipo_shares_total: int = 0
    ipo_shares_remaining: int = 0
    ipo_start_at: datetime = Field(default_factory=datetime.utcnow)
    ipo_end_at: datetime = Field(default_factory=datetime.utcnow)

    market_cap: float = 10000000.0  # current_price * total_shares
    volume_24h: int = 0  # Shares traded in last 24h
    
    # Engagement metrics (affect price)
    upvotes: int = 0
    downvotes: int = 0
    comments_count: int = 0
    reports_count: int = 0
    shares_count: int = 0  # Social shares
    
    # Lists of user IDs who engaged
    upvoted_by: List[str] = []
    downvoted_by: List[str] = []
    reported_by: List[str] = []
    
    # Status
    trend_status: TrendStatus = TrendStatus.STABLE
    is_active: bool = True
    is_featured: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Comments stored inline (for simplicity)
    comments: List[Comment] = []
    
    # Price history (last 30 data points)
    price_history: List[dict] = []  # [{timestamp, price}]


class MemeResponse(BaseModel):
    """Meme response for API."""
    id: str
    name: str
    ticker: str
    description: str
    image_url: str
    category: str
    creator_username: str
    
    current_price: float
    previous_price: float
    price_change_24h: float
    price_change_percent_24h: float
    
    total_shares: int
    available_shares: int
    market_cap: float
    volume_24h: int
    
    upvotes: int
    downvotes: int
    comments_count: int
    
    trend_status: str
    is_featured: bool
    
    created_at: datetime
    
    # IPO Data
    ipo_price: Optional[float] = None
    ipo_shares_remaining: Optional[int] = None
    ipo_end_at: Optional[datetime] = None
    ipo_shares_total: Optional[int] = None
    
    # User's interaction status (filled per-user)
    user_has_upvoted: bool = False
    user_has_downvoted: bool = False
    user_owns_shares: int = 0


class MemeListResponse(BaseModel):
    """Response for meme list with pagination."""
    memes: List[MemeResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ============ Price Update Rules ============
"""
PRICE CHANGE RULES:
1. Upvote: +0.5% to price
2. Downvote: -0.3% to price
3. Comment: +0.1% to price (engagement boost)
4. Report: -1% to price (if >5 reports, -5%)
5. Buy: +0.2% per 100 shares bought
6. Sell: -0.2% per 100 shares sold
7. Social Share: +0.05% to price

TREND STATUS:
- HOT: >10% gain in 24h
- COLD: >10% loss in 24h
- VOLATILE: >5% swings both ways in 24h
- STABLE: <5% change in 24h
"""
