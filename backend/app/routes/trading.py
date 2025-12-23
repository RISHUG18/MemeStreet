from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from app.core.security import get_current_user_id
from app.models.transaction import TransactionCreate, TransactionResponse, TransactionType
from app.services.trading_service import (
    execute_trade, get_user_transactions, get_user_portfolio_value,
    get_user_open_orders, cancel_order
)
from app.services.user_service import get_user_by_id

router = APIRouter(prefix="/trading", tags=["Trading"])


@router.post("/buy", response_model=dict)
async def buy_shares(
    meme_id: str,
    quantity: int = Query(..., ge=1),
    max_price: Optional[float] = Query(None, gt=0),
    user_id: str = Depends(get_current_user_id)
):
    """Buy shares of a meme stock."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    trade = TransactionCreate(
        meme_id=meme_id,
        transaction_type=TransactionType.BUY,
        quantity=quantity,
        limit_price=max_price,
    )
    
    try:
        transaction, new_balance = await execute_trade(user_id, user["username"], trade)
        is_listing = getattr(transaction, "status", "") == "pending"
        return {
            "success": True,
            "message": (
                f"Placed a buy order for {quantity} shares!" if is_listing else f"Successfully bought {quantity} shares!"
            ),
            "transaction": transaction,
            "new_balance": new_balance
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell", response_model=dict)
async def sell_shares(
    meme_id: str,
    quantity: int = Query(..., ge=1),
    min_price: Optional[float] = Query(None, gt=0),
    user_id: str = Depends(get_current_user_id)
):
    """Sell shares of a meme stock."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    trade = TransactionCreate(
        meme_id=meme_id,
        transaction_type=TransactionType.SELL,
        quantity=quantity,
        limit_price=min_price,
    )
    
    try:
        transaction, new_balance = await execute_trade(user_id, user["username"], trade)
        is_listing = getattr(transaction, "status", "") == "pending"
        return {
            "success": True,
            "message": (
                f"Listed {quantity} shares for sale!" if is_listing else f"Successfully sold {quantity} shares!"
            ),
            "transaction": transaction,
            "new_balance": new_balance
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=dict)
async def get_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    transaction_type: Optional[str] = None,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's transaction history."""
    transactions, total = await get_user_transactions(
        user_id, page, per_page, transaction_type
    )
    
    return {
        "transactions": transactions,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }


@router.get("/portfolio", response_model=dict)
async def get_portfolio(
    user_id: str = Depends(get_current_user_id)
):
    """Get user's portfolio with current values."""
    try:
        portfolio = await get_user_portfolio_value(user_id)
        orders = await get_user_open_orders(user_id)
        portfolio["open_orders"] = orders
        return portfolio
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/orders/{order_id}/cancel", response_model=dict)
async def cancel_user_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Cancel an open order."""
    try:
        success = await cancel_order(user_id, order_id)
        return {"success": success, "message": "Order cancelled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balance", response_model=dict)
async def get_balance(
    user_id: str = Depends(get_current_user_id)
):
    """Get user's wallet balance."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "balance": user.get("wallet_balance", 0),
        "currency": "USD"
    }
