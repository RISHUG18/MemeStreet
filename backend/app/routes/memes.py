from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from app.core.security import get_current_user_id, get_optional_user_id
from app.models.meme import MemeCreate, MemeResponse, MemeListResponse, MemeCategory
from app.models.transaction import EngagementAction, EngagementResponse, EngagementType
from app.services.meme_service import (
    create_meme, get_meme_by_id, get_meme_by_ticker, get_all_memes,
    upvote_meme, downvote_meme, add_comment, report_meme,
    get_meme_comments, get_trending_memes, get_featured_memes,
    seed_sample_memes,
    is_ipo_active, calculate_intrinsic_value, get_trading_band,
)
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/memes", tags=["Memes"])


@router.get("", response_model=MemeListResponse)
@router.get("/", response_model=MemeListResponse)
async def list_memes(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    sort_by: str = Query("market_cap", regex="^(market_cap|price|volume|change|upvotes|newest)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    search: Optional[str] = None,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Get all memes with pagination and filters."""
    memes, total = await get_all_memes(
        page=page,
        per_page=per_page,
        category=category,
        sort_by=sort_by,
        sort_order=sort_order,
        search=search,
        user_id=user_id
    )
    
    total_pages = (total + per_page - 1) // per_page
    
    return MemeListResponse(
        memes=memes,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/trending", response_model=list[MemeResponse])
async def get_trending():
    """Get trending memes."""
    return await get_trending_memes(limit=10)


@router.get("/featured", response_model=list[MemeResponse])
async def get_featured():
    """Get featured memes."""
    return await get_featured_memes(limit=5)


@router.get("/categories")
async def get_categories():
    """Get all meme categories."""
    return [{"value": c.value, "label": c.value.title()} for c in MemeCategory]


@router.get("/{meme_id}/trading-band")
async def get_meme_trading_band(meme_id: str):
    """
    Get the trading band for a meme (Post-IPO price limits).
    Returns intrinsic value and min/max allowed listing prices.
    """
    meme = await get_meme_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    
    intrinsic = calculate_intrinsic_value(meme)
    min_price, max_price = get_trading_band(meme)
    ipo_active = is_ipo_active(meme)
    
    return {
        "meme_id": meme_id,
        "intrinsic_value": round(intrinsic, 2),
        "min_allowed_price": round(min_price, 2),
        "max_allowed_price": round(max_price, 2),
        "current_price": round(float(meme.get("current_price", 0)), 2),
        "ipo_active": ipo_active,
        "upvotes": meme.get("upvotes", 0),
        "comments_count": meme.get("comments_count", 0),
    }


@router.get("/{meme_id}", response_model=MemeResponse)
async def get_meme(
    meme_id: str,
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """Get a specific meme by ID."""
    meme = await get_meme_by_id(meme_id)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    
    # Get user's holdings if logged in
    user_owns = 0
    user_upvoted = False
    user_downvoted = False
    
    if user_id:
        from app.core.database import get_database
        from bson import ObjectId
        db = get_database()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            portfolio = user.get("portfolio", [])
            holding = next((p for p in portfolio if p["meme_id"] == meme_id), None)
            if holding:
                user_owns = holding["quantity_owned"]
        
        user_upvoted = user_id in meme.get("upvoted_by", [])
        user_downvoted = user_id in meme.get("downvoted_by", [])
    
    # Determine buyable supply for UI.
    available_shares = int(meme.get("available_shares", 0))
    if meme.get("ipo_end_at") is not None and meme.get("ipo_shares_remaining") is not None and meme.get("ipo_price") is not None:
        if is_ipo_active(meme):
            available_shares = int(meme.get("ipo_shares_remaining", 0))
        else:
            from app.core.database import get_database
            db = get_database()
            try:
                row = await db.orders.aggregate([
                    {"$match": {"type": "sell", "status": "open", "meme_id": meme_id}},
                    {"$group": {"_id": "$meme_id", "total": {"$sum": "$quantity_remaining"}}},
                ]).to_list(length=1)
                available_shares = int(row[0]["total"]) if row else 0
            except Exception:
                available_shares = 0

    return MemeResponse(
        id=meme["id"],
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
        user_has_upvoted=user_upvoted,
        user_has_downvoted=user_downvoted,
        user_owns_shares=user_owns
    )


@router.get("/ticker/{ticker}", response_model=MemeResponse)
async def get_meme_by_ticker_route(ticker: str):
    """Get a meme by ticker symbol."""
    meme = await get_meme_by_ticker(ticker)
    if not meme:
        raise HTTPException(status_code=404, detail="Meme not found")
    
    available_shares = int(meme.get("available_shares", 0))
    if meme.get("ipo_end_at") is not None and meme.get("ipo_shares_remaining") is not None and meme.get("ipo_price") is not None:
        if is_ipo_active(meme):
            available_shares = int(meme.get("ipo_shares_remaining", 0))
        else:
            from app.core.database import get_database
            db = get_database()
            try:
                row = await db.orders.aggregate([
                    {"$match": {"type": "sell", "status": "open", "meme_id": meme["id"]}},
                    {"$group": {"_id": "$meme_id", "total": {"$sum": "$quantity_remaining"}}},
                ]).to_list(length=1)
                available_shares = int(row[0]["total"]) if row else 0
            except Exception:
                available_shares = 0

    return MemeResponse(
        id=meme["id"],
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
    )


@router.post("/", response_model=MemeResponse)
async def create_new_meme(
    meme_data: MemeCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new meme stock (requires authentication)."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        meme = await create_meme(meme_data, user_id, user["username"])
        return MemeResponse(
            id=meme.id,
            name=meme.name,
            ticker=meme.ticker,
            description=meme.description,
            image_url=meme.image_url,
            category=meme.category.value if hasattr(meme.category, 'value') else meme.category,
            creator_username=meme.creator_username,
            current_price=meme.current_price,
            previous_price=meme.previous_price,
            price_change_24h=meme.price_change_24h,
            price_change_percent_24h=meme.price_change_percent_24h,
            total_shares=meme.total_shares,
            available_shares=meme.available_shares,
            market_cap=meme.market_cap,
            volume_24h=meme.volume_24h,
            upvotes=meme.upvotes,
            downvotes=meme.downvotes,
            comments_count=meme.comments_count,
            trend_status=meme.trend_status.value if hasattr(meme.trend_status, 'value') else meme.trend_status,
            is_featured=meme.is_featured,
            created_at=meme.created_at,
            ipo_price=meme.ipo_price,
            ipo_shares_remaining=meme.ipo_shares_remaining,
            ipo_end_at=meme.ipo_end_at,
            ipo_shares_total=meme.ipo_shares_total,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{meme_id}/upvote", response_model=EngagementResponse)
async def upvote(
    meme_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Upvote a meme (increases price by 0.5%)."""
    try:
        success, new_price, change, percent = await upvote_meme(meme_id, user_id)
        return EngagementResponse(
            success=success,
            message="Upvoted!" if success else "Removed upvote",
            new_price=new_price,
            price_change=change,
            price_change_percent=percent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{meme_id}/downvote", response_model=EngagementResponse)
async def downvote(
    meme_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Downvote a meme (decreases price by 0.3%)."""
    try:
        success, new_price, change, percent = await downvote_meme(meme_id, user_id)
        return EngagementResponse(
            success=success,
            message="Downvoted!" if success else "Removed downvote",
            new_price=new_price,
            price_change=change,
            price_change_percent=percent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{meme_id}/comment", response_model=EngagementResponse)
async def comment(
    meme_id: str,
    content: str,
    user_id: str = Depends(get_current_user_id)
):
    """Add a comment to a meme (increases price by 0.1%)."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        comment_obj, new_price, change, percent = await add_comment(
            meme_id, user_id, user["username"], content
        )
        return EngagementResponse(
            success=True,
            message="Comment added!",
            new_price=new_price,
            price_change=change,
            price_change_percent=percent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{meme_id}/report", response_model=EngagementResponse)
async def report(
    meme_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Report a meme (decreases price by 1-5%)."""
    try:
        success, new_price, change, percent = await report_meme(meme_id, user_id)
        if not success:
            return EngagementResponse(
                success=False,
                message="You've already reported this meme",
                new_price=new_price,
                price_change=0,
                price_change_percent=0
            )
        return EngagementResponse(
            success=True,
            message="Meme reported!",
            new_price=new_price,
            price_change=change,
            price_change_percent=percent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{meme_id}/comments")
async def get_comments(
    meme_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get comments for a meme."""
    try:
        comments, total = await get_meme_comments(meme_id, page, per_page)
        return {
            "comments": comments,
            "total": total,
            "page": page,
            "per_page": per_page
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/seed")
async def seed_memes():
    """Seed sample memes (for testing)."""
    await seed_sample_memes()
    return {"message": "Sample memes seeded!"}
