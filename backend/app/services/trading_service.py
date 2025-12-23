from datetime import datetime
from typing import Optional, List, Tuple
from bson import ObjectId

from app.core.config import settings
from app.core.database import get_database
from app.services.meme_service import get_meme_by_id, update_meme_price
from app.services.meme_service import is_ipo_active, calculate_intrinsic_value, get_trading_band
from app.models.transaction import (
    TransactionCreate, TransactionInDB, TransactionResponse,
    TransactionType, TransactionStatus
)


def _is_legacy_market(meme: dict) -> bool:
    """Legacy market = system is always the counterparty (pre-IPO schema memes)."""
    return meme.get("ipo_end_at") is None or meme.get("ipo_shares_remaining") is None or meme.get("ipo_price") is None


async def _set_meme_trade_price(
    meme_id: str,
    trade_price: float,
    quantity: int,
    supply_before: Optional[int] = None,
    supply_added: Optional[int] = None,
) -> None:
    """Set market price from last trade (secondary market) with demand/supply + engagement adjustments."""
    db = get_database()
    meme = await get_meme_by_id(meme_id)
    if not meme:
        raise ValueError("Meme not found")

    old_price = float(meme.get("current_price", trade_price))

    base_price = max(0.01, float(trade_price))

    # Demand vs supply: how much of the visible orderbook was consumed by this buy.
    demand_boost = 0.0
    if supply_before is not None and int(supply_before) > 0:
        ratio = max(0.0, min(1.0, float(quantity) / float(supply_before)))
        # Only boost when demand is meaningfully high.
        demand_boost = max(0.0, 2.0 * ratio - 1.0)  # 0..1

    # New supply pressure: listing new sell orders can soften price.
    supply_pressure = 0.0
    if supply_added is not None and int(supply_added) > 0:
        before = max(0, int(supply_before or 0))
        added = int(supply_added)
        if before <= 0:
            supply_pressure = 1.0
        else:
            supply_pressure = max(0.0, min(1.0, float(added) / float(before)))

    # Engagement sentiment: likes/dislikes + small positive contribution from comments.
    upvotes = float(meme.get("upvotes", 0) or 0)
    downvotes = float(meme.get("downvotes", 0) or 0)
    comments = float(meme.get("comments_count", 0) or 0)
    denom = max(1.0, upvotes + downvotes + comments)
    engagement_score = ((upvotes - downvotes) + (float(settings.POST_IPO_COMMENTS_WEIGHT) * comments)) / denom
    engagement_score = max(-1.0, min(1.0, engagement_score))

    adj = (
        (float(settings.POST_IPO_DEMAND_FACTOR) * demand_boost)
        - (float(settings.POST_IPO_SUPPLY_FACTOR) * supply_pressure)
        + (float(settings.POST_IPO_ENGAGEMENT_FACTOR) * engagement_score)
    )
    new_price = max(0.01, round(base_price * (1.0 + adj), 4))
    price_change = new_price - old_price
    price_change_percent = (price_change / old_price * 100) if old_price > 0 else 0

    price_history = meme.get("price_history", [])
    price_history.append({"timestamp": datetime.utcnow().isoformat(), "price": new_price})
    price_history = price_history[-100:]

    await db.memes.update_one(
        {"_id": ObjectId(meme_id)},
        {
            "$set": {
                "previous_price": old_price,
                "current_price": new_price,
                "price_change_24h": float(meme.get("price_change_24h", 0.0)) + price_change,
                "price_change_percent_24h": price_change_percent,
                "all_time_high": max(float(meme.get("all_time_high", new_price)), new_price),
                "all_time_low": min(float(meme.get("all_time_low", new_price)), new_price),
                "market_cap": new_price * int(meme.get("total_shares", 0)),
                "price_history": price_history,
                "updated_at": datetime.utcnow(),
            },
            "$inc": {"volume_24h": int(quantity)},
        }
    )


async def _upsert_portfolio_buy(user_id: str, meme_id: str, buy_qty: int, price_per_share: float) -> None:
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    portfolio = user.get("portfolio", [])
    holding = next((p for p in portfolio if p["meme_id"] == meme_id), None)
    total_cost = price_per_share * buy_qty

    if holding:
        new_qty = int(holding.get("quantity_owned", 0)) + buy_qty
        prev_avg = float(holding.get("average_buy_price", 0))
        prev_qty = int(holding.get("quantity_owned", 0))
        new_avg = ((prev_avg * prev_qty) + (price_per_share * buy_qty)) / new_qty
        new_investment = new_avg * new_qty
        await db.users.update_one(
            {"_id": ObjectId(user_id), "portfolio.meme_id": meme_id},
            {
                "$set": {
                    "portfolio.$.quantity_owned": new_qty,
                    "portfolio.$.average_buy_price": new_avg,
                    "portfolio.$.total_investment_value": new_investment,
                }
            },
        )
    else:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {
                    "portfolio": {
                        "meme_id": meme_id,
                        "quantity_owned": buy_qty,
                        "average_buy_price": price_per_share,
                        "total_investment_value": total_cost,
                    }
                }
            },
        )


async def _decrement_portfolio_for_sell(user_id: str, meme_id: str, sell_qty: int) -> None:
    db = get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")

    portfolio = user.get("portfolio", [])
    holding = next((p for p in portfolio if p["meme_id"] == meme_id), None)
    if not holding or int(holding.get("quantity_owned", 0)) < sell_qty:
        owned = int(holding.get("quantity_owned", 0)) if holding else 0
        raise ValueError(f"Not enough shares to sell. You own {owned} shares.")

    new_qty = int(holding.get("quantity_owned", 0)) - sell_qty
    avg_buy = float(holding.get("average_buy_price", 0))
    new_investment = avg_buy * new_qty

    if new_qty == 0:
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"portfolio": {"meme_id": meme_id}}},
        )
    else:
        await db.users.update_one(
            {"_id": ObjectId(user_id), "portfolio.meme_id": meme_id},
            {
                "$set": {
                    "portfolio.$.quantity_owned": new_qty,
                    "portfolio.$.total_investment_value": new_investment,
                }
            },
        )


async def execute_trade(
    user_id: str,
    username: str,
    trade: TransactionCreate
) -> Tuple[TransactionResponse, float]:
    """
    Execute a buy or sell trade.
    Returns: (transaction, new_balance)
    """
    db = get_database()
    
    # Get meme
    meme = await get_meme_by_id(trade.meme_id)
    if not meme:
        raise ValueError("Meme not found")
    
    # Get user
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")
    
    # Legacy path keeps existing behavior for older memes in DB.
    if _is_legacy_market(meme):
        current_price = meme["current_price"]
        total_cost = current_price * trade.quantity

        # Get user's current holding of this meme
        portfolio = user.get("portfolio", [])
        current_holding = next(
            (p for p in portfolio if p["meme_id"] == trade.meme_id),
            None
        )

        if trade.transaction_type == TransactionType.BUY:
            # Check if user has enough balance
            if user.get("wallet_balance", 0) < total_cost:
                raise ValueError(f"Insufficient balance. Need ${total_cost:.2f}, have ${user.get('wallet_balance', 0):.2f}")

            # Check if enough shares available
            if meme["available_shares"] < trade.quantity:
                raise ValueError(f"Not enough shares available. Only {meme['available_shares']} left.")

            # Deduct balance
            new_balance = user["wallet_balance"] - total_cost

            # Update user's portfolio
            if current_holding:
                # Update existing holding
                new_quantity = current_holding["quantity_owned"] + trade.quantity
                new_avg_price = (
                    (current_holding["average_buy_price"] * current_holding["quantity_owned"]) +
                    (current_price * trade.quantity)
                ) / new_quantity
                new_investment = new_avg_price * new_quantity

                await db.users.update_one(
                    {"_id": ObjectId(user_id), "portfolio.meme_id": trade.meme_id},
                    {
                        "$set": {
                            "wallet_balance": new_balance,
                            "portfolio.$.quantity_owned": new_quantity,
                            "portfolio.$.average_buy_price": new_avg_price,
                            "portfolio.$.total_investment_value": new_investment,
                        }
                    }
                )
            else:
                # Add new holding
                new_holding = {
                    "meme_id": trade.meme_id,
                    "quantity_owned": trade.quantity,
                    "average_buy_price": current_price,
                    "total_investment_value": total_cost,
                }
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {"wallet_balance": new_balance},
                        "$push": {"portfolio": new_holding}
                    }
                )

            # Update meme's available shares
            await db.memes.update_one(
                {"_id": ObjectId(trade.meme_id)},
                {
                    "$inc": {
                        "available_shares": -trade.quantity,
                        "volume_24h": trade.quantity
                    }
                }
            )

            # Update price (buying increases price)
            await update_meme_price(trade.meme_id, "buy", trade.quantity)

        else:  # SELL
            # Check if user has enough shares
            if not current_holding or current_holding["quantity_owned"] < trade.quantity:
                owned = current_holding["quantity_owned"] if current_holding else 0
                raise ValueError(f"Not enough shares to sell. You own {owned} shares.")

            # Add to balance
            new_balance = user["wallet_balance"] + total_cost

            # Update portfolio
            new_quantity = current_holding["quantity_owned"] - trade.quantity

            if new_quantity == 0:
                # Remove from portfolio
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {"wallet_balance": new_balance},
                        "$pull": {"portfolio": {"meme_id": trade.meme_id}}
                    }
                )
            else:
                # Update holding
                new_investment = current_holding["average_buy_price"] * new_quantity
                await db.users.update_one(
                    {"_id": ObjectId(user_id), "portfolio.meme_id": trade.meme_id},
                    {
                        "$set": {
                            "wallet_balance": new_balance,
                            "portfolio.$.quantity_owned": new_quantity,
                            "portfolio.$.total_investment_value": new_investment,
                        }
                    }
                )

            # Update meme's available shares
            await db.memes.update_one(
                {"_id": ObjectId(trade.meme_id)},
                {
                    "$inc": {
                        "available_shares": trade.quantity,
                        "volume_24h": trade.quantity
                    }
                }
            )

            # Update price (selling decreases price)
            await update_meme_price(trade.meme_id, "sell", trade.quantity)

        # Create transaction record
        transaction = {
            "user_id": user_id,
            "username": username,
            "meme_id": trade.meme_id,
            "meme_ticker": meme["ticker"],
            "meme_name": meme["name"],
            "transaction_type": trade.transaction_type.value,
            "quantity": trade.quantity,
            "price_per_share": current_price,
            "total_value": total_cost,
            "status": TransactionStatus.COMPLETED.value,
            "created_at": datetime.utcnow(),
        }

        result = await db.transactions.insert_one(transaction)
        transaction["id"] = str(result.inserted_id)

        # Update user's total trades count
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_trades": 1}}
        )
        
        # Update meme's total trades count (for hype score / dynamic band)
        await db.memes.update_one(
            {"_id": ObjectId(trade.meme_id)},
            {"$inc": {"total_trades": 1}}
        )

        return TransactionResponse(
            id=transaction["id"],
            meme_ticker=transaction["meme_ticker"],
            meme_name=transaction["meme_name"],
            transaction_type=transaction["transaction_type"],
            quantity=transaction["quantity"],
            price_per_share=transaction["price_per_share"],
            total_value=transaction["total_value"],
            status=transaction["status"],
            created_at=transaction["created_at"]
        ), new_balance


    # New market:
    # - IPO window: buy from system at fixed IPO price (20% pool)
    # - Post-IPO: bid/ask orderbook (users list buy orders + sell orders)

    if trade.transaction_type == TransactionType.BUY:
        if is_ipo_active(meme):
            ipo_price = float(meme["ipo_price"])
            total_cost = ipo_price * trade.quantity

            if user.get("wallet_balance", 0) < total_cost:
                raise ValueError(f"Insufficient balance. Need ${total_cost:.2f}, have ${user.get('wallet_balance', 0):.2f}")

            if int(meme.get("ipo_shares_remaining", 0)) < trade.quantity:
                raise ValueError(f"Not enough IPO shares available. Only {int(meme.get('ipo_shares_remaining', 0))} left.")

            new_balance = float(user.get("wallet_balance", 0)) - total_cost

            # Deduct buyer balance
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"wallet_balance": new_balance}},
            )

            # Credit creator with IPO proceeds (issuer revenue)
            creator_id = meme.get("creator_id")
            if creator_id:
                try:
                    await db.users.update_one(
                        {"_id": ObjectId(str(creator_id))},
                        {"$inc": {"wallet_balance": total_cost}},
                    )
                except Exception:
                    pass

            # Update buyer portfolio using IPO price
            await _upsert_portfolio_buy(user_id, trade.meme_id, trade.quantity, ipo_price)

            # Decrement IPO pool
            await db.memes.update_one(
                {"_id": ObjectId(trade.meme_id)},
                {
                    "$inc": {
                        "ipo_shares_remaining": -trade.quantity,
                        "available_shares": -trade.quantity,
                        "volume_24h": trade.quantity,
                        "total_trades": 1,  # Increment meme's trade count for hype score
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            # Apply rules to market price (even though fill price is fixed)
            await update_meme_price(trade.meme_id, "buy", trade.quantity)

            transaction_doc = {
                "user_id": user_id,
                "username": username,
                "meme_id": trade.meme_id,
                "meme_ticker": meme["ticker"],
                "meme_name": meme["name"],
                "transaction_type": TransactionType.BUY.value,
                "quantity": trade.quantity,
                "price_per_share": ipo_price,
                "total_value": total_cost,
                "status": TransactionStatus.COMPLETED.value,
                "created_at": datetime.utcnow(),
            }
            result = await db.transactions.insert_one(transaction_doc)
            transaction_id = str(result.inserted_id)

            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"total_trades": 1}},
            )

            return TransactionResponse(
                id=transaction_id,
                meme_ticker=transaction_doc["meme_ticker"],
                meme_name=transaction_doc["meme_name"],
                transaction_type=transaction_doc["transaction_type"],
                quantity=transaction_doc["quantity"],
                price_per_share=transaction_doc["price_per_share"],
                total_value=transaction_doc["total_value"],
                status=transaction_doc["status"],
                created_at=transaction_doc["created_at"],
            ), new_balance

        # Secondary BUY: always create a buy order (bid) listing first, then match asks if available.
        bid_price = float(trade.limit_price) if trade.limit_price is not None else float(meme.get("current_price", 0))
        if bid_price <= 0:
            raise ValueError("Max price must be greater than 0")

        total_qty = int(trade.quantity)
        if total_qty <= 0:
            raise ValueError("Quantity must be positive")

        # Trading band enforcement for Post-IPO buy orders
        intrinsic = calculate_intrinsic_value(meme)
        min_price, max_price = get_trading_band(meme)
        hype_score = int(meme.get("total_trades", 0) or 0)
        
        if bid_price < min_price:
            raise ValueError(f"Bid price ${bid_price:.2f} is below minimum ${min_price:.2f} (50% of intrinsic ${intrinsic:.2f})")
        if bid_price > max_price:
            raise ValueError(f"Bid price ${bid_price:.2f} exceeds max ${max_price:.2f} (intrinsic ${intrinsic:.2f} × {2.0 + hype_score * 0.05:.2f} hype multiplier)")

        reserve_total = bid_price * total_qty
        buyer_balance = float(user.get("wallet_balance", 0))
        if buyer_balance < reserve_total:
            raise ValueError(f"Insufficient balance. Need ${reserve_total:.2f}, have ${buyer_balance:.2f}")

        # Escrow full bid amount
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"wallet_balance": buyer_balance - reserve_total}},
        )

        # Create the buy order listing up-front (even if it ends up filling immediately)
        buy_order_doc = {
            "type": "buy",
            "status": "open",
            "meme_id": trade.meme_id,
            "buyer_id": user_id,
            "buyer_username": username,
            "price": bid_price,
            "quantity_total": total_qty,
            "quantity_remaining": total_qty,
            "reserved_total": reserve_total,
            "reserved_remaining": reserve_total,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        buy_order_res = await db.orders.insert_one(buy_order_doc)
        buy_order_id = buy_order_res.inserted_id

        # Orderbook supply snapshot (all asks)
        orders_all = await db.orders.find(
            {"meme_id": trade.meme_id, "type": "sell", "status": "open"}
        ).sort([("price", 1), ("created_at", 1)]).to_list(length=500)
        total_available = sum(int(o.get("quantity_remaining", 0)) for o in orders_all)

        # Only match asks priced <= bid
        orders = [o for o in orders_all if float(o.get("price", 0)) <= bid_price]

        qty_needed = total_qty
        fills = []  # (order, fill_qty)
        running_cost = 0.0
        last_trade_price = bid_price
        for o in orders:
            if qty_needed <= 0:
                break
            available = int(o.get("quantity_remaining", 0))
            if available <= 0:
                continue
            take = min(available, qty_needed)
            price = float(o.get("price", 0))
            fills.append((o, take))
            running_cost += price * take
            last_trade_price = price
            qty_needed -= take

        filled_qty = total_qty - qty_needed

        # Apply fills
        if filled_qty > 0:
            avg_fill_price = running_cost / filled_qty
            await _upsert_portfolio_buy(user_id, trade.meme_id, filled_qty, avg_fill_price)

            maker_fee_bps = int(getattr(settings, "MAKER_FEE_BPS", 0) or 0)
            burn_share_bps = int(getattr(settings, "BURN_SHARE_BPS", 0) or 0)
            creator_share_bps = int(getattr(settings, "CREATOR_FEE_SHARE_BPS", 0) or 0)

            for (o, take) in fills:
                seller_id = o.get("seller_id")
                price = float(o.get("price", 0))
                payout_gross = price * take

                fee_total = max(0.0, payout_gross * maker_fee_bps / 10000.0)
                fee_burn = max(0.0, fee_total * burn_share_bps / 10000.0)
                fee_remaining = max(0.0, fee_total - fee_burn)
                fee_creator = max(0.0, fee_remaining * creator_share_bps / 10000.0)
                fee_treasury = max(0.0, fee_remaining - fee_creator)
                payout_net = max(0.0, payout_gross - fee_total)

                if seller_id:
                    await db.users.update_one(
                        {"_id": ObjectId(str(seller_id))},
                        {"$inc": {"wallet_balance": payout_net}},
                    )

                if fee_total > 0:
                    creator_id = meme.get("creator_id")
                    if creator_id and fee_creator > 0:
                        try:
                            await db.users.update_one(
                                {"_id": ObjectId(str(creator_id))},
                                {"$inc": {"wallet_balance": fee_creator}},
                            )
                        except Exception:
                            pass

                    await db.treasury.update_one(
                        {"_id": settings.TREASURY_DOC_ID},
                        {
                            "$inc": {
                                "total_fees": fee_total,
                                "burned_fees": fee_burn,
                                "creator_fees": fee_creator,
                                "treasury_fees": fee_treasury,
                            },
                            "$set": {"updated_at": datetime.utcnow()},
                            "$setOnInsert": {"created_at": datetime.utcnow()},
                        },
                        upsert=True,
                    )

                await db.orders.update_one(
                    {"_id": o["_id"]},
                    {"$inc": {"quantity_remaining": -take}, "$set": {"updated_at": datetime.utcnow()}},
                )
                if int(o.get("quantity_remaining", 0)) - take <= 0:
                    await db.orders.update_one(
                        {"_id": o["_id"]},
                        {"$set": {"status": "filled", "updated_at": datetime.utcnow()}},
                    )

                # Buyer refund: bid - execution
                refund = max(0.0, (bid_price - price) * take)
                if refund > 0:
                    await db.users.update_one(
                        {"_id": ObjectId(user_id)},
                        {"$inc": {"wallet_balance": refund}},
                    )

                # Decrement our buy order remaining/reserved by the reserved amount for the filled shares
                await db.orders.update_one(
                    {"_id": buy_order_id},
                    {
                        "$inc": {
                            "quantity_remaining": -take,
                            "reserved_remaining": -(bid_price * take),
                        },
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )

                # Record seller-side completed transaction
                if seller_id:
                    await db.transactions.insert_one(
                        {
                            "user_id": str(seller_id),
                            "username": o.get("seller_username", ""),
                            "meme_id": trade.meme_id,
                            "meme_ticker": meme["ticker"],
                            "meme_name": meme["name"],
                            "transaction_type": TransactionType.SELL.value,
                            "quantity": take,
                            "price_per_share": price,
                            "total_value": payout_net,
                            "gross_value": payout_gross,
                            "fee_paid": fee_total,
                            "fee_burned": fee_burn,
                            "fee_to_creator": fee_creator,
                            "fee_to_treasury": fee_treasury,
                            "status": TransactionStatus.COMPLETED.value,
                            "created_at": datetime.utcnow(),
                        }
                    )

            await _set_meme_trade_price(trade.meme_id, last_trade_price, filled_qty, supply_before=total_available)
            
            # Increment meme's total trades for hype score
            await db.memes.update_one(
                {"_id": ObjectId(trade.meme_id)},
                {"$inc": {"total_trades": 1}}
            )

            buyer_tx = {
                "user_id": user_id,
                "username": username,
                "meme_id": trade.meme_id,
                "meme_ticker": meme["ticker"],
                "meme_name": meme["name"],
                "transaction_type": TransactionType.BUY.value,
                "quantity": filled_qty,
                "price_per_share": avg_fill_price,
                "total_value": running_cost,
                "status": TransactionStatus.COMPLETED.value,
                "created_at": datetime.utcnow(),
            }
            buyer_res = await db.transactions.insert_one(buyer_tx)
            completed_tx_id = str(buyer_res.inserted_id)
        else:
            completed_tx_id = None

        # Remaining qty stays open on the original buy order
        remaining_qty = qty_needed
        if remaining_qty > 0:
            # Ensure reserved_remaining matches remaining quantity at the bid price
            await db.orders.update_one(
                {"_id": buy_order_id},
                {
                    "$set": {
                        "quantity_remaining": remaining_qty,
                        "reserved_remaining": bid_price * remaining_qty,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

            tx_doc = {
                "user_id": user_id,
                "username": username,
                "meme_id": trade.meme_id,
                "meme_ticker": meme["ticker"],
                "meme_name": meme["name"],
                "transaction_type": TransactionType.BUY.value,
                "quantity": remaining_qty,
                "price_per_share": bid_price,
                "total_value": bid_price * remaining_qty,
                "status": TransactionStatus.PENDING.value,
                "created_at": datetime.utcnow(),
            }
            tx_res = await db.transactions.insert_one(tx_doc)

            new_user = await db.users.find_one({"_id": ObjectId(user_id)})
            new_balance = float(new_user.get("wallet_balance", 0)) if new_user else 0.0

            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"total_trades": 1}},
            )

            return TransactionResponse(
                id=str(tx_res.inserted_id),
                meme_ticker=tx_doc["meme_ticker"],
                meme_name=tx_doc["meme_name"],
                transaction_type=tx_doc["transaction_type"],
                quantity=tx_doc["quantity"],
                price_per_share=tx_doc["price_per_share"],
                total_value=tx_doc["total_value"],
                status=tx_doc["status"],
                created_at=tx_doc["created_at"],
            ), new_balance

        # Fully filled: mark buy order filled (so a listing record still exists)
        await db.orders.update_one(
            {"_id": buy_order_id},
            {"$set": {"status": "filled", "quantity_remaining": 0, "reserved_remaining": 0.0, "updated_at": datetime.utcnow()}},
        )

        new_user = await db.users.find_one({"_id": ObjectId(user_id)})
        new_balance = float(new_user.get("wallet_balance", 0)) if new_user else 0.0

        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_trades": 1}},
        )

        return TransactionResponse(
            id=completed_tx_id or str(ObjectId()),
            meme_ticker=meme["ticker"],
            meme_name=meme["name"],
            transaction_type=TransactionType.BUY.value,
            quantity=filled_qty,
            price_per_share=(running_cost / filled_qty) if filled_qty > 0 else bid_price,
            total_value=running_cost,
            status=TransactionStatus.COMPLETED.value,
            created_at=datetime.utcnow(),
        ), new_balance

    # SELL
    if is_ipo_active(meme):
        raise ValueError("Selling is disabled during the initial offering window")

    # Post-IPO SELL: always create a sell order listing first, then match against highest bids.
    sell_qty = int(trade.quantity)
    if sell_qty <= 0:
        raise ValueError("Quantity must be positive")

    # Trading band enforcement for Post-IPO listings
    intrinsic = calculate_intrinsic_value(meme)
    min_price, max_price = get_trading_band(meme)
    
    default_price = float(meme.get("current_price", 0))
    list_price = float(trade.limit_price) if trade.limit_price is not None else default_price
    if list_price <= 0:
        raise ValueError("Listing price must be greater than 0")
    
    # Enforce trading band: price must be within dynamic band
    # min = 0.5 * intrinsic, max = intrinsic * (2.0 + hype_score * 0.05)
    hype_score = int(meme.get("total_trades", 0) or 0)
    if list_price < min_price:
        raise ValueError(f"Listing price ${list_price:.2f} is below minimum ${min_price:.2f} (50% of intrinsic ${intrinsic:.2f})")
    if list_price > max_price:
        raise ValueError(f"Listing price ${list_price:.2f} exceeds max ${max_price:.2f} (intrinsic ${intrinsic:.2f} × {2.0 + hype_score * 0.05:.2f} hype multiplier)")

    # Supply snapshot before listing (used to soften price when supply increases).
    supply_before = 0
    try:
        pipeline = [
            {"$match": {"meme_id": trade.meme_id, "type": "sell", "status": "open"}},
            {"$group": {"_id": None, "total": {"$sum": "$quantity_remaining"}}},
        ]
        rows = await db.orders.aggregate(pipeline).to_list(length=1)
        if rows:
            supply_before = int(rows[0].get("total", 0) or 0)
    except Exception:
        supply_before = 0

    # Move shares into escrow by decrementing seller portfolio now.
    await _decrement_portfolio_for_sell(user_id, trade.meme_id, sell_qty)

    # Create the sell order listing up-front (even if it ends up filling immediately)
    sell_order_doc = {
        "type": "sell",
        "status": "open",
        "meme_id": trade.meme_id,
        "seller_id": user_id,
        "seller_username": username,
        "price": list_price,
        "quantity_total": sell_qty,
        "quantity_remaining": sell_qty,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    sell_order_res = await db.orders.insert_one(sell_order_doc)
    sell_order_id = sell_order_res.inserted_id

    bids = await db.orders.find(
        {"meme_id": trade.meme_id, "type": "buy", "status": "open", "price": {"$gte": list_price}}
    ).sort([("price", -1), ("created_at", 1)]).to_list(length=500)

    qty_left = sell_qty
    filled_qty = 0
    proceeds_gross = 0.0
    proceeds_net_total = 0.0
    last_trade_price = list_price

    maker_fee_bps = int(getattr(settings, "MAKER_FEE_BPS", 0) or 0)
    burn_share_bps = int(getattr(settings, "BURN_SHARE_BPS", 0) or 0)
    creator_share_bps = int(getattr(settings, "CREATOR_FEE_SHARE_BPS", 0) or 0)

    for b in bids:
        if qty_left <= 0:
            break
        available = int(b.get("quantity_remaining", 0))
        if available <= 0:
            continue
        take = min(available, qty_left)
        price = float(b.get("price", 0))
        if price <= 0:
            continue

        trade_value = price * take
        proceeds_gross += trade_value
        filled_qty += take
        qty_left -= take
        last_trade_price = price

        fee_total = max(0.0, trade_value * maker_fee_bps / 10000.0)
        fee_burn = max(0.0, fee_total * burn_share_bps / 10000.0)
        fee_remaining = max(0.0, fee_total - fee_burn)
        fee_creator = max(0.0, fee_remaining * creator_share_bps / 10000.0)
        fee_treasury = max(0.0, fee_remaining - fee_creator)
        payout_net = max(0.0, trade_value - fee_total)
        proceeds_net_total += payout_net

        # Credit seller
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"wallet_balance": payout_net}},
        )

        if fee_total > 0:
            creator_id = meme.get("creator_id")
            if creator_id and fee_creator > 0:
                try:
                    await db.users.update_one(
                        {"_id": ObjectId(str(creator_id))},
                        {"$inc": {"wallet_balance": fee_creator}},
                    )
                except Exception:
                    pass
            await db.treasury.update_one(
                {"_id": settings.TREASURY_DOC_ID},
                {
                    "$inc": {
                        "total_fees": fee_total,
                        "burned_fees": fee_burn,
                        "creator_fees": fee_creator,
                        "treasury_fees": fee_treasury,
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                    "$setOnInsert": {"created_at": datetime.utcnow()},
                },
                upsert=True,
            )

        # Update buy order (reduce quantity and reserved)
        await db.orders.update_one(
            {"_id": b["_id"]},
            {
                "$inc": {
                    "quantity_remaining": -take,
                    "reserved_remaining": -(price * take),
                },
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
        if int(b.get("quantity_remaining", 0)) - take <= 0:
            await db.orders.update_one(
                {"_id": b["_id"]},
                {"$set": {"status": "filled", "updated_at": datetime.utcnow()}},
            )

        buyer_id = b.get("buyer_id")
        buyer_username = b.get("buyer_username", "")
        if buyer_id:
            await _upsert_portfolio_buy(str(buyer_id), trade.meme_id, take, price)
            await db.transactions.insert_one(
                {
                    "user_id": str(buyer_id),
                    "username": buyer_username,
                    "meme_id": trade.meme_id,
                    "meme_ticker": meme["ticker"],
                    "meme_name": meme["name"],
                    "transaction_type": TransactionType.BUY.value,
                    "quantity": take,
                    "price_per_share": price,
                    "total_value": trade_value,
                    "status": TransactionStatus.COMPLETED.value,
                    "created_at": datetime.utcnow(),
                }
            )

        # Decrement our sell order remaining
        await db.orders.update_one(
            {"_id": sell_order_id},
            {"$inc": {"quantity_remaining": -take}, "$set": {"updated_at": datetime.utcnow()}},
        )

    if filled_qty > 0:
        await _set_meme_trade_price(trade.meme_id, last_trade_price, filled_qty)
        
        # Increment meme's total trades for hype score
        await db.memes.update_one(
            {"_id": ObjectId(trade.meme_id)},
            {"$inc": {"total_trades": 1}}
        )

    listed_qty = qty_left
    if listed_qty > 0:
        # Keep the existing sell order open with remaining quantity
        await db.orders.update_one(
            {"_id": sell_order_id},
            {"$set": {"quantity_remaining": listed_qty, "updated_at": datetime.utcnow()}},
        )

        # Apply supply-side price pressure only for newly listed remainder.
        try:
            await _set_meme_trade_price(
                trade.meme_id,
                float(meme.get("current_price", 0.01)),
                0,
                supply_before=supply_before,
                supply_added=listed_qty,
            )
        except Exception:
            pass

        tx_doc = {
            "user_id": user_id,
            "username": username,
            "meme_id": trade.meme_id,
            "meme_ticker": meme["ticker"],
            "meme_name": meme["name"],
            "transaction_type": TransactionType.SELL.value,
            "quantity": listed_qty,
            "price_per_share": list_price,
            "total_value": list_price * listed_qty,
            "status": TransactionStatus.PENDING.value,
            "created_at": datetime.utcnow(),
        }
        tx_res = await db.transactions.insert_one(tx_doc)

        new_user = await db.users.find_one({"_id": ObjectId(user_id)})
        new_balance = float(new_user.get("wallet_balance", 0)) if new_user else float(user.get("wallet_balance", 0))

        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_trades": 1}},
        )

        return TransactionResponse(
            id=str(tx_res.inserted_id),
            meme_ticker=tx_doc["meme_ticker"],
            meme_name=tx_doc["meme_name"],
            transaction_type=tx_doc["transaction_type"],
            quantity=tx_doc["quantity"],
            price_per_share=tx_doc["price_per_share"],
            total_value=tx_doc["total_value"],
            status=tx_doc["status"],
            created_at=tx_doc["created_at"],
        ), new_balance

    # Fully filled immediately
    if filled_qty > 0:
        await db.orders.update_one(
            {"_id": sell_order_id},
            {"$set": {"status": "filled", "quantity_remaining": 0, "updated_at": datetime.utcnow()}},
        )

        seller_tx = {
            "user_id": user_id,
            "username": username,
            "meme_id": trade.meme_id,
            "meme_ticker": meme["ticker"],
            "meme_name": meme["name"],
            "transaction_type": TransactionType.SELL.value,
            "quantity": filled_qty,
            "price_per_share": (proceeds_gross / filled_qty) if filled_qty > 0 else last_trade_price,
            "total_value": proceeds_net_total,
            "status": TransactionStatus.COMPLETED.value,
            "created_at": datetime.utcnow(),
        }
        tx_res = await db.transactions.insert_one(seller_tx)

        new_user = await db.users.find_one({"_id": ObjectId(user_id)})
        new_balance = float(new_user.get("wallet_balance", 0)) if new_user else float(user.get("wallet_balance", 0))

        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"total_trades": 1}},
        )

        return TransactionResponse(
            id=str(tx_res.inserted_id),
            meme_ticker=seller_tx["meme_ticker"],
            meme_name=seller_tx["meme_name"],
            transaction_type=seller_tx["transaction_type"],
            quantity=seller_tx["quantity"],
            price_per_share=seller_tx["price_per_share"],
            total_value=seller_tx["total_value"],
            status=seller_tx["status"],
            created_at=seller_tx["created_at"],
        ), new_balance

    # No bids matched: keep the sell order open at full remaining quantity and create a pending transaction for visibility
    tx_doc = {
        "user_id": user_id,
        "username": username,
        "meme_id": trade.meme_id,
        "meme_ticker": meme["ticker"],
        "meme_name": meme["name"],
        "transaction_type": TransactionType.SELL.value,
        "quantity": sell_qty,
        "price_per_share": list_price,
        "total_value": list_price * sell_qty,
        "status": TransactionStatus.PENDING.value,
        "created_at": datetime.utcnow(),
    }
    tx_res = await db.transactions.insert_one(tx_doc)

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"total_trades": 1}},
    )

    return TransactionResponse(
        id=str(tx_res.inserted_id),
        meme_ticker=tx_doc["meme_ticker"],
        meme_name=tx_doc["meme_name"],
        transaction_type=tx_doc["transaction_type"],
        quantity=tx_doc["quantity"],
        price_per_share=tx_doc["price_per_share"],
        total_value=tx_doc["total_value"],
        status=tx_doc["status"],
        created_at=tx_doc["created_at"],
    ), float(user.get("wallet_balance", 0))
    



async def get_user_transactions(
    user_id: str,
    page: int = 1,
    per_page: int = 20,
    transaction_type: Optional[str] = None
) -> Tuple[List[TransactionResponse], int]:
    """Get user's transaction history."""
    db = get_database()
    
    query = {"user_id": user_id}
    if transaction_type:
        query["transaction_type"] = transaction_type
    
    total = await db.transactions.count_documents(query)
    
    cursor = db.transactions.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page)
    transactions = await cursor.to_list(length=per_page)
    
    return [
        TransactionResponse(
            id=str(t["_id"]),
            meme_ticker=t["meme_ticker"],
            meme_name=t["meme_name"],
            transaction_type=t["transaction_type"],
            quantity=t["quantity"],
            price_per_share=t["price_per_share"],
            total_value=t["total_value"],
            status=t["status"],
            created_at=t["created_at"]
        ) for t in transactions
    ], total


async def get_meme_transactions(
    meme_id: str,
    page: int = 1,
    per_page: int = 20
) -> Tuple[List[TransactionResponse], int]:
    """Get all transactions for a specific meme."""
    db = get_database()
    
    query = {"meme_id": meme_id}
    total = await db.transactions.count_documents(query)
    
    cursor = db.transactions.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page)
    transactions = await cursor.to_list(length=per_page)
    
    return [
        TransactionResponse(
            id=str(t["_id"]),
            meme_ticker=t["meme_ticker"],
            meme_name=t["meme_name"],
            transaction_type=t["transaction_type"],
            quantity=t["quantity"],
            price_per_share=t["price_per_share"],
            total_value=t["total_value"],
            status=t["status"],
            created_at=t["created_at"]
        ) for t in transactions
    ], total


async def get_user_portfolio_value(user_id: str) -> dict:
    """Calculate user's total portfolio value."""
    db = get_database()
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found")
    
    portfolio = user.get("portfolio", [])
    total_value = 0
    total_invested = 0
    holdings = []
    
    for holding in portfolio:
        meme = await get_meme_by_id(holding["meme_id"])
        if meme:
            current_value = meme["current_price"] * holding["quantity_owned"]
            invested = holding["total_investment_value"]
            profit_loss = current_value - invested
            profit_loss_percent = (profit_loss / invested * 100) if invested > 0 else 0
            
            holdings.append({
                "meme_id": holding["meme_id"],
                "meme_ticker": meme["ticker"],
                "meme_name": meme["name"],
                "quantity": holding["quantity_owned"],
                "average_buy_price": holding["average_buy_price"],
                "current_price": meme["current_price"],
                "current_value": current_value,
                "invested": invested,
                "profit_loss": profit_loss,
                "profit_loss_percent": profit_loss_percent,
            })
            
            total_value += current_value
            total_invested += invested
    
    return {
        "wallet_balance": user.get("wallet_balance", 0),
        "portfolio_value": total_value,
        "total_invested": total_invested,
        "total_profit_loss": total_value - total_invested,
        "total_profit_loss_percent": ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0,
        "holdings": holdings,
    }


async def get_user_open_orders(user_id: str) -> List[dict]:
    """Get user's open orders."""
    db = get_database()
    orders = []
    async for order in db.orders.find({
        "$or": [{"buyer_id": user_id}, {"seller_id": user_id}],
        "status": "open"
    }).sort("created_at", -1):
        meme = await get_meme_by_id(order["meme_id"])
        orders.append({
            "id": str(order["_id"]),
            "type": order["type"],
            "meme_id": order["meme_id"],
            "meme_ticker": meme["ticker"] if meme else "UNKNOWN",
            "meme_name": meme["name"] if meme else "Unknown",
            "price": order["price"],
            "quantity": order["quantity_remaining"],
            "total": order["price"] * order["quantity_remaining"],
            "created_at": order["created_at"]
        })
    return orders


async def cancel_order(user_id: str, order_id: str) -> bool:
    """Cancel an open order."""
    db = get_database()
    order = await db.orders.find_one({"_id": ObjectId(order_id), "status": "open"})
    if not order:
        raise ValueError("Order not found or already filled/cancelled")
    
    # Verify ownership
    if order.get("buyer_id") != user_id and order.get("seller_id") != user_id:
        raise ValueError("Not authorized to cancel this order")
    
    if order["type"] == "buy":
        # Refund reserved amount
        refund = float(order.get("reserved_remaining", 0))
        if refund > 0:
            await db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$inc": {"wallet_balance": refund}}
            )
    else:
        # Return shares to portfolio
        meme_id = order["meme_id"]
        qty = int(order.get("quantity_remaining", 0))
        if qty > 0:
            # Check if holding exists
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            portfolio = user.get("portfolio", [])
            holding = next((p for p in portfolio if p["meme_id"] == meme_id), None)
            
            if holding:
                await db.users.update_one(
                    {"_id": ObjectId(user_id), "portfolio.meme_id": meme_id},
                    {"$inc": {"portfolio.$.quantity_owned": qty}}
                )
            else:
                # Should not happen for sell order, but handle it
                # We need average buy price. Use current price or 0?
                # Ideally we should have stored original avg price in order, but we didn't.
                # We'll use 0 or current price.
                meme = await get_meme_by_id(meme_id)
                price = meme["current_price"] if meme else 0
                await db.users.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$push": {
                            "portfolio": {
                                "meme_id": meme_id,
                                "quantity_owned": qty,
                                "average_buy_price": price,
                                "total_investment_value": price * qty
                            }
                        }
                    }
                )
    
    # Mark as cancelled
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
    )
    
    return True
