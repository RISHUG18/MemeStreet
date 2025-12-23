from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from bson import ObjectId
import random
import uuid

from app.core.database import get_database
from app.core.config import settings
from app.models.meme import (
    MemeCreate, MemeInDB, MemeResponse, MemeCategory, TrendStatus, Comment
)


def is_ipo_active(meme: dict, now: Optional[datetime] = None) -> bool:
    """True if meme is currently in its initial fixed-price offering window."""
    if not meme:
        return False

    ipo_end_at = meme.get("ipo_end_at")
    remaining = meme.get("ipo_shares_remaining")

    if ipo_end_at is None or remaining is None:
        return False

    now = now or datetime.utcnow()
    return now < ipo_end_at and remaining > 0


def is_ipo_window(meme: dict, now: Optional[datetime] = None) -> bool:
    """True if still within the IPO time window (regardless of remaining shares)."""
    if not meme:
        return False

    ipo_end_at = meme.get("ipo_end_at")
    if ipo_end_at is None:
        return False

    now = now or datetime.utcnow()
    return now < ipo_end_at


# ============ Intrinsic Value Calculation ============
def calculate_intrinsic_value(meme: dict) -> float:
    """
    Calculate intrinsic value based on engagement.
    Formula: BASE + (Upvotes * UPVOTE_WEIGHT) + (Comments * COMMENT_WEIGHT)
    """
    base = float(settings.INTRINSIC_BASE_PRICE)
    upvotes = int(meme.get("upvotes", 0) or 0)
    comments = int(meme.get("comments_count", 0) or 0)
    
    intrinsic = base + (upvotes * float(settings.INTRINSIC_UPVOTE_WEIGHT)) + (comments * float(settings.INTRINSIC_COMMENT_WEIGHT))
    return max(0.01, round(intrinsic, 4))


def get_trading_band(meme: dict) -> Tuple[float, float]:
    """
    Get the min and max listing prices for post-IPO trading.
    
    Dynamic Band Rules:
    - min_price = 0.5 * Intrinsic Value (prevents total crash)
    - max_price = Intrinsic Value * (2.0 + (hype_score * 0.05))
    
    Where hype_score = total number of completed trades for this meme.
    The more people trade, the higher the max price ceiling can go.
    """
    intrinsic = calculate_intrinsic_value(meme)
    
    # Min price is always 50% of intrinsic (floor)
    min_price = max(0.01, round(intrinsic * float(settings.TRADING_BAND_MIN_MULTIPLIER), 4))
    
    # Max price is dynamic based on hype (trade volume)
    # hype_score = total completed trades
    hype_score = int(meme.get("total_trades", 0) or 0)
    hype_multiplier = float(settings.TRADING_BAND_BASE_MAX_MULTIPLIER) + (hype_score * float(settings.TRADING_BAND_HYPE_FACTOR))
    
    max_price = max(min_price, round(intrinsic * hype_multiplier, 4))
    return (min_price, max_price)


def get_market_status(meme: dict) -> str:
    """
    Get market status: 'IPO' or 'OPEN_MARKET'
    IPO = shares available to buy from system
    OPEN_MARKET = peer-to-peer trading only
    """
    ipo_remaining = int(meme.get("ipo_shares_remaining", 0) or 0)
    return "IPO" if ipo_remaining > 0 else "OPEN_MARKET"


async def create_meme(meme_data: MemeCreate, user_id: str, username: str) -> MemeInDB:
    """Create a new meme stock."""
    db = get_database()
    
    # Check if ticker already exists
    existing = await db.memes.find_one({"ticker": meme_data.ticker.upper()})
    if existing:
        raise ValueError(f"Ticker ${meme_data.ticker.upper()} already exists")
    
    now = datetime.utcnow()

    ipo_percent = float(meme_data.ipo_percent) if getattr(meme_data, "ipo_percent", None) is not None else float(settings.IPO_PERCENT)
    ipo_percent = max(0.0, min(1.0, ipo_percent))
    ipo_duration_minutes = int(meme_data.ipo_duration_minutes) if getattr(meme_data, "ipo_duration_minutes", None) is not None else int(settings.IPO_DURATION_MINUTES)

    ipo_shares_total = max(1, int(meme_data.total_shares * ipo_percent))
    ipo_shares_total = min(ipo_shares_total, meme_data.total_shares)
    creator_shares = max(0, meme_data.total_shares - ipo_shares_total)

    # If the creator isn't a real user document, don't strand supply.
    try:
        creator_exists = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        creator_exists = None
    if not creator_exists:
        ipo_shares_total = meme_data.total_shares
        creator_shares = 0
    ipo_end_at = now + timedelta(minutes=ipo_duration_minutes)

    meme_dict = {
        "name": meme_data.name,
        "ticker": meme_data.ticker.upper(),
        "description": meme_data.description,
        "image_url": meme_data.image_url,
        "category": meme_data.category.value,
        "creator_id": user_id,
        "creator_username": username,
        
        # Price & Market
        "current_price": meme_data.initial_price,
        "previous_price": meme_data.initial_price,
        "price_change_24h": 0.0,
        "price_change_percent_24h": 0.0,
        "all_time_high": meme_data.initial_price,
        "all_time_low": meme_data.initial_price,
        
        # Supply
        "total_shares": meme_data.total_shares,
        # During IPO, only the IPO pool is buyable from the system.
        "available_shares": ipo_shares_total,
        "ipo_price": meme_data.initial_price,
        "ipo_percent": ipo_percent,
        "ipo_duration_minutes": ipo_duration_minutes,
        "ipo_shares_total": ipo_shares_total,
        "ipo_shares_remaining": ipo_shares_total,
        "ipo_start_at": now,
        "ipo_end_at": ipo_end_at,
        "market_cap": meme_data.initial_price * meme_data.total_shares,
        "volume_24h": 0,
        
        # Engagement
        "upvotes": 0,
        "downvotes": 0,
        "comments_count": 0,
        "reports_count": 0,
        "shares_count": 0,
        
        "upvoted_by": [],
        "downvoted_by": [],
        "reported_by": [],

        # IPO anti-spam: apply vote price moves in batches
        "ipo_upvote_steps_applied": 0,
        "ipo_downvote_steps_applied": 0,
        
        # Status
        "trend_status": TrendStatus.STABLE.value,
        "is_active": True,
        "is_featured": False,
        
        # Timestamps
        "created_at": now,
        "updated_at": now,
        
        # Comments & History
        "comments": [],
        "price_history": [{"timestamp": now.isoformat(), "price": meme_data.initial_price}],
    }
    
    result = await db.memes.insert_one(meme_dict)
    meme_dict["id"] = str(result.inserted_id)

    # Allocate remaining supply to creator so post-IPO trading is buyer<->seller.
    if creator_shares > 0 and creator_exists:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {
                    "portfolio": {
                        "meme_id": meme_dict["id"],
                        "quantity_owned": creator_shares,
                        "average_buy_price": meme_data.initial_price,
                        "total_investment_value": meme_data.initial_price * creator_shares,
                    }
                }
            }
        )
    
    return MemeInDB(**meme_dict)


async def get_meme_by_id(meme_id: str) -> Optional[dict]:
    """Get a meme by its ID."""
    db = get_database()
    meme = await db.memes.find_one({"_id": ObjectId(meme_id)})
    if meme:
        meme["id"] = str(meme["_id"])
    return meme


async def get_meme_by_ticker(ticker: str) -> Optional[dict]:
    """Get a meme by its ticker symbol."""
    db = get_database()
    meme = await db.memes.find_one({"ticker": ticker.upper()})
    if meme:
        meme["id"] = str(meme["_id"])
    return meme


async def get_all_memes(
    page: int = 1,
    per_page: int = 20,
    category: Optional[str] = None,
    sort_by: str = "market_cap",
    sort_order: str = "desc",
    search: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[List[MemeResponse], int]:
    """Get all memes with pagination and filters."""
    db = get_database()
    
    # Build query
    query = {"is_active": True}
    
    if category:
        query["category"] = category
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"ticker": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]
    
    # Sort direction
    sort_dir = -1 if sort_order == "desc" else 1
    
    # Sort field mapping
    sort_fields = {
        "market_cap": "market_cap",
        "price": "current_price",
        "volume": "volume_24h",
        "change": "price_change_percent_24h",
        "upvotes": "upvotes",
        "newest": "created_at",
    }
    sort_field = sort_fields.get(sort_by, "market_cap")
    
    # Get total count
    total = await db.memes.count_documents(query)
    
    # Get memes
    cursor = db.memes.find(query).sort(sort_field, sort_dir).skip((page - 1) * per_page).limit(per_page)
    memes = await cursor.to_list(length=per_page)

    # For post-IPO memes, available shares come from open sell orders (secondary market).
    meme_ids = [str(m["_id"]) for m in memes]
    order_supply: dict[str, int] = {}
    if meme_ids:
        try:
            pipeline = [
                {"$match": {"type": "sell", "status": "open", "meme_id": {"$in": meme_ids}}},
                {"$group": {"_id": "$meme_id", "total": {"$sum": "$quantity_remaining"}}},
            ]
            async for row in db.orders.aggregate(pipeline):
                order_supply[str(row.get("_id"))] = int(row.get("total", 0))
        except Exception:
            order_supply = {}
    
    # Get user's portfolio if user_id provided
    user_holdings = {}
    if user_id:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user and "portfolio" in user:
            for item in user.get("portfolio", []):
                user_holdings[item["meme_id"]] = item["quantity_owned"]
    
    # Convert to response
    meme_responses = []
    for meme in memes:
        meme_id = str(meme["_id"])

        # Determine buyable supply for UI.
        if meme.get("ipo_end_at") is None or meme.get("ipo_shares_remaining") is None or meme.get("ipo_price") is None:
            available_shares = int(meme.get("available_shares", 0))
        elif is_ipo_active(meme):
            available_shares = int(meme.get("ipo_shares_remaining", 0))
        else:
            available_shares = int(order_supply.get(meme_id, 0))

        meme_responses.append(MemeResponse(
            id=meme_id,
            name=meme["name"],
            ticker=meme["ticker"],
            description=meme["description"],
            image_url=meme["image_url"],
            category=meme["category"],
            creator_username=meme["creator_username"],
            current_price=meme["current_price"],
            previous_price=meme["previous_price"],
            price_change_24h=meme["price_change_24h"],
            price_change_percent_24h=meme["price_change_percent_24h"],
            total_shares=meme["total_shares"],
            available_shares=available_shares,
            market_cap=meme["market_cap"],
            volume_24h=meme["volume_24h"],
            upvotes=meme["upvotes"],
            downvotes=meme["downvotes"],
            comments_count=meme["comments_count"],
            trend_status=meme["trend_status"],
            is_featured=meme["is_featured"],
            created_at=meme["created_at"],
            ipo_price=meme.get("ipo_price"),
            ipo_shares_remaining=meme.get("ipo_shares_remaining"),
            ipo_end_at=meme.get("ipo_end_at"),
            ipo_shares_total=meme.get("ipo_shares_total"),
            user_has_upvoted=user_id in meme.get("upvoted_by", []) if user_id else False,
            user_has_downvoted=user_id in meme.get("downvoted_by", []) if user_id else False,
            user_owns_shares=user_holdings.get(meme_id, 0)
        ))
    
    return meme_responses, total


async def update_meme_price_from_engagement(meme_id: str) -> Tuple[float, float, float]:
    """
    Update meme price based on engagement (intrinsic value formula).
    Price = BASE + (Upvotes * 0.5) + (Comments * 0.3)
    Returns: (new_price, price_change, price_change_percent)
    """
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    
    if not meme:
        raise ValueError("Meme not found")
    
    old_price = float(meme.get("current_price", 0.01))
    
    # Calculate new price from intrinsic value
    new_price = calculate_intrinsic_value(meme)
    
    price_change = new_price - old_price
    price_change_percent = (price_change / old_price * 100) if old_price > 0 else 0
    
    # Update ATH/ATL
    all_time_high = max(float(meme.get("all_time_high", new_price)), new_price)
    all_time_low = min(float(meme.get("all_time_low", new_price)), new_price)
    
    # Add to price history
    price_history = meme.get("price_history", [])
    price_history.append({"timestamp": datetime.utcnow().isoformat(), "price": new_price})
    price_history = price_history[-100:]
    
    # Update trend status
    trend_status = calculate_trend_status(old_price, new_price, float(meme.get("price_change_24h", 0)))
    
    # Update in DB
    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {
            "$set": {
                "current_price": new_price,
                "previous_price": old_price,
                "price_change_24h": float(meme.get("price_change_24h", 0)) + price_change,
                "price_change_percent_24h": price_change_percent,
                "all_time_high": all_time_high,
                "all_time_low": all_time_low,
                "market_cap": new_price * int(meme.get("total_shares", 0)),
                "trend_status": trend_status,
                "price_history": price_history,
                "updated_at": datetime.utcnow(),
            }
        }
    )
    
    return new_price, price_change, price_change_percent


# Keep old function for backward compatibility but redirect to new logic
async def update_meme_price(meme_id: str, change_type: str, quantity: int = 1) -> Tuple[float, float, float]:
    """
    Update meme price based on action type.
    Now redirects to engagement-based pricing.
    """
    return await update_meme_price_from_engagement(meme_id)


def calculate_trend_status(old_price: float, new_price: float, change_24h: float) -> str:
    """Calculate the trend status based on price changes."""
    percent_change = ((new_price - old_price) / old_price) * 100 if old_price > 0 else 0
    
    if abs(percent_change) > 10:
        if percent_change > 0:
            return TrendStatus.HOT.value
        else:
            return TrendStatus.COLD.value
    elif abs(percent_change) > 5:
        return TrendStatus.VOLATILE.value
    else:
        return TrendStatus.STABLE.value


# Note: _apply_vote_price_batches is deprecated - now using update_meme_price_from_engagement
# for engagement-based pricing (Price = BASE + upvotes * UPVOTE_WEIGHT + comments * COMMENT_WEIGHT)


async def upvote_meme(meme_id: str, user_id: str) -> Tuple[bool, float, float, float]:
    """
    Upvote a meme. Price updates based on engagement formula.
    Returns (success, new_price, price_change, price_change_percent)
    """
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    
    if not meme:
        raise ValueError("Meme not found")
    
    upvoted_by = meme.get("upvoted_by", [])
    downvoted_by = meme.get("downvoted_by", [])

    # Toggle off if already upvoted
    if user_id in upvoted_by:
        await db.memes.update_one(
            {"_id": ObjectId(meme_id)},
            {"$pull": {"upvoted_by": user_id}, "$inc": {"upvotes": -1}}
        )
        new_price, change, percent = await update_meme_price_from_engagement(meme_id)
        return False, new_price, change, percent

    # Switch from downvote -> upvote
    if user_id in downvoted_by:
        await db.memes.update_one(
            {"_id": ObjectId(meme_id)},
            {
                "$pull": {"downvoted_by": user_id},
                "$addToSet": {"upvoted_by": user_id},
                "$inc": {"downvotes": -1, "upvotes": 1},
            }
        )
        new_price, change, percent = await update_meme_price_from_engagement(meme_id)
        return True, new_price, change, percent

    # Add upvote
    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {"$addToSet": {"upvoted_by": user_id}, "$inc": {"upvotes": 1}}
    )
    new_price, change, percent = await update_meme_price_from_engagement(meme_id)
    return True, new_price, change, percent


async def downvote_meme(meme_id: str, user_id: str) -> Tuple[bool, float, float, float]:
    """
    Downvote a meme. Note: Downvotes don't affect intrinsic value in current formula.
    Returns (success, new_price, price_change, price_change_percent)
    """
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    
    if not meme:
        raise ValueError("Meme not found")
    
    upvoted_by = meme.get("upvoted_by", [])
    downvoted_by = meme.get("downvoted_by", [])

    # Toggle off if already downvoted
    if user_id in downvoted_by:
        await db.memes.update_one(
            {"_id": ObjectId(meme_id)},
            {"$pull": {"downvoted_by": user_id}, "$inc": {"downvotes": -1}}
        )
        # Price doesn't change from downvotes, but we still return current price
        updated = await get_meme_by_id(meme_id)
        return False, float(updated.get("current_price", 0)), 0.0, 0.0

    # Switch from upvote -> downvote (removes upvote which does affect price)
    if user_id in upvoted_by:
        await db.memes.update_one(
            {"_id": ObjectId(meme_id)},
            {
                "$pull": {"upvoted_by": user_id},
                "$addToSet": {"downvoted_by": user_id},
                "$inc": {"upvotes": -1, "downvotes": 1},
            }
        )
        new_price, change, percent = await update_meme_price_from_engagement(meme_id)
        return True, new_price, change, percent

    # Add downvote (doesn't affect price in current formula)
    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {"$addToSet": {"downvoted_by": user_id}, "$inc": {"downvotes": 1}}
    )
    updated = await get_meme_by_id(meme_id)
    return True, float(updated.get("current_price", 0)), 0.0, 0.0


async def add_comment(meme_id: str, user_id: str, username: str, content: str) -> Tuple[Comment, float, float, float]:
    """Add a comment to a meme. Price updates based on engagement formula."""
    db = get_database()
    
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "username": username,
        "content": content,
        "created_at": datetime.utcnow(),
        "likes": 0
    }
    
    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {
            "$push": {"comments": comment},
            "$inc": {"comments_count": 1}
        }
    )
    
    # Use engagement-based pricing
    new_price, change, percent = await update_meme_price_from_engagement(meme_id)
    
    return Comment(**comment), new_price, change, percent


async def report_meme(meme_id: str, user_id: str) -> Tuple[bool, float, float, float]:
    """Report a meme."""
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    
    if not meme:
        raise ValueError("Meme not found")
    
    # Check if already reported
    if user_id in meme.get("reported_by", []):
        return False, meme["current_price"], 0, 0
    
    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {
            "$push": {"reported_by": user_id},
            "$inc": {"reports_count": 1}
        }
    )
    
    new_price, change, percent = await update_meme_price(meme_id, "report")
    return True, new_price, change, percent


async def get_meme_comments(meme_id: str, page: int = 1, per_page: int = 20) -> Tuple[List[Comment], int]:
    """Get comments for a meme with pagination."""
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    
    if not meme:
        raise ValueError("Meme not found")
    
    comments = meme.get("comments", [])
    total = len(comments)
    
    # Sort by newest first and paginate
    comments = sorted(comments, key=lambda x: x.get("created_at", datetime.min), reverse=True)
    start = (page - 1) * per_page
    end = start + per_page
    
    return [Comment(**c) for c in comments[start:end]], total


async def get_trending_memes(limit: int = 10) -> List[MemeResponse]:
    """Get trending memes (highest 24h volume and price change)."""
    memes, _ = await get_all_memes(
        page=1,
        per_page=limit,
        sort_by="volume",
        sort_order="desc"
    )
    return memes


async def get_featured_memes(limit: int = 5) -> List[MemeResponse]:
    """Get featured memes."""
    db = get_database()
    cursor = db.memes.find({"is_featured": True, "is_active": True}).limit(limit)
    memes = await cursor.to_list(length=limit)
    
    return [MemeResponse(
        id=str(m["_id"]),
        name=m["name"],
        ticker=m["ticker"],
        description=m["description"],
        image_url=m["image_url"],
        category=m["category"],
        creator_username=m["creator_username"],
        current_price=m["current_price"],
        previous_price=m["previous_price"],
        price_change_24h=m["price_change_24h"],
        price_change_percent_24h=m["price_change_percent_24h"],
        total_shares=m["total_shares"],
        available_shares=m["available_shares"],
        market_cap=m["market_cap"],
        volume_24h=m["volume_24h"],
        upvotes=m["upvotes"],
        downvotes=m["downvotes"],
        comments_count=m["comments_count"],
        trend_status=m["trend_status"],
        is_featured=m["is_featured"],
        created_at=m["created_at"],
    ) for m in memes]


async def seed_sample_memes():
    """Seed some sample memes for testing."""
    db = get_database()
    
    # Check if memes already exist
    count = await db.memes.count_documents({})
    if count > 0:
        return
    
    sample_memes = [
        {
            "name": "Doge",
            "ticker": "DOGE",
            "description": "Much wow, very meme. The OG meme coin dog.",
            "image_url": "https://i.imgflip.com/4t0m5.jpg",
            "category": "crypto",
            "initial_price": 42.0
        },
        {
            "name": "Pepe",
            "ticker": "PEPE",
            "description": "Feels good man. The internet's favorite frog.",
            "image_url": "https://i.imgflip.com/39t1o.jpg",
            "category": "pepe",
            "initial_price": 15.0
        },
        {
            "name": "Stonks",
            "ticker": "STONK",
            "description": "When you make financial decisions.",
            "image_url": "https://i.imgflip.com/3lw3cd.jpg",
            "category": "stonks",
            "initial_price": 100.0
        },
        {
            "name": "Wojak",
            "ticker": "WOJK",
            "description": "I know that feel bro.",
            "image_url": "https://i.imgflip.com/1otk96.jpg",
            "category": "wojak",
            "initial_price": 8.0
        },
        {
            "name": "This Is Fine",
            "ticker": "FINE",
            "description": "Everything is fine. The dog in the burning house.",
            "image_url": "https://i.imgflip.com/wxica.jpg",
            "category": "other",
            "initial_price": 25.0
        },
        {
            "name": "Distracted Boyfriend",
            "ticker": "DBFRD",
            "description": "When you see something better.",
            "image_url": "https://i.imgflip.com/1ur9b0.jpg",
            "category": "other",
            "initial_price": 35.0
        },
        {
            "name": "Drake Hotline",
            "ticker": "DRAKE",
            "description": "Nah / Yeah - the classic preference meme.",
            "image_url": "https://i.imgflip.com/30b1gx.jpg",
            "category": "other",
            "initial_price": 50.0
        },
        {
            "name": "Two Buttons",
            "ticker": "2BTN",
            "description": "The hardest choices require the strongest wills.",
            "image_url": "https://i.imgflip.com/1g8my4.jpg",
            "category": "other",
            "initial_price": 18.0
        },
    ]
    
    for meme_data in sample_memes:
        meme = MemeCreate(
            name=meme_data["name"],
            ticker=meme_data["ticker"],
            description=meme_data["description"],
            image_url=meme_data["image_url"],
            category=MemeCategory(meme_data["category"]),
            initial_price=meme_data["initial_price"]
        )
        await create_meme(meme, "system", "MemeStreet")
    
    print(f"Seeded {len(sample_memes)} sample memes!")


async def migrate_legacy_memes():
    """
    Migrate legacy memes (without IPO fields) to work with the orderbook system.
    Sets ipo_end_at to a past date so they're treated as post-IPO memes.
    """
    db = get_database()
    
    # Find memes without IPO fields
    legacy_memes = await db.memes.find({
        "$or": [
            {"ipo_end_at": {"$exists": False}},
            {"ipo_end_at": None},
            {"ipo_price": {"$exists": False}},
            {"ipo_price": None},
        ]
    }).to_list(length=1000)
    
    if not legacy_memes:
        return
    
    now = datetime.utcnow()
    past_date = now - timedelta(days=365)  # Set IPO end to 1 year ago
    
    migrated = 0
    for meme in legacy_memes:
        current_price = float(meme.get("current_price", 10.0))
        total_shares = int(meme.get("total_shares", 1000000))
        
        update_data = {
            "ipo_price": current_price,
            "ipo_percent": 0.0,  # No IPO shares left
            "ipo_duration_minutes": 0,
            "ipo_shares_total": 0,
            "ipo_shares_remaining": 0,
            "ipo_start_at": past_date,
            "ipo_end_at": past_date,
            "vote_upvote_steps_applied": 0,
            "vote_downvote_steps_applied": 0,
        }
        
        await db.memes.update_one(
            {"_id": meme["_id"]},
            {"$set": update_data}
        )
        migrated += 1
    
    if migrated > 0:
        print(f"Migrated {migrated} legacy memes to orderbook system!")
