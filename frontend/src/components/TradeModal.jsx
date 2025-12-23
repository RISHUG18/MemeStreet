import React, { useState, useEffect, useRef } from 'react';
import { 
  X, TrendingUp, TrendingDown, DollarSign, 
  AlertCircle, CheckCircle, Loader, Minus, Plus
} from 'lucide-react';
import { tradingService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './TradeModal.css';

function TradeModal({ meme, type, onClose, onComplete }) {
  const { user, updateUser } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [maxPrice, setMaxPrice] = useState(() => {
    const n = Number(meme?.current_price);
    return Number.isFinite(n) && n > 0 ? n : 0;
  });
  const [minPrice, setMinPrice] = useState(() => {
    const n = Number(meme?.current_price);
    return Number.isFinite(n) && n > 0 ? n : 0;
  });
  const [balance, setBalance] = useState(() => {
    const n = Number(user?.wallet_balance);
    return Number.isFinite(n) ? n : 0;
  });
  const hasFetchedBalanceRef = useRef(false);
  const [loading, setLoading] = useState(false);
  const [loadingBalance, setLoadingBalance] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const isBuying = type === 'buy';

  const ipoEndAt = meme?.ipo_end_at ? new Date(meme.ipo_end_at) : null;
  const ipoSharesRemaining = Number(meme?.ipo_shares_remaining);
  const hasIpoTime = ipoEndAt instanceof Date && !Number.isNaN(ipoEndAt.getTime());
  const isIpoActive = !!(hasIpoTime && ipoEndAt.getTime() > Date.now() && (Number.isFinite(ipoSharesRemaining) ? ipoSharesRemaining > 0 : true));
  const ipoPrice = Number(meme?.ipo_price);
  const effectiveBuyPrice = (isIpoActive && Number.isFinite(ipoPrice) && ipoPrice > 0) ? ipoPrice : meme.current_price;

  const effectiveMaxBuyPrice = isIpoActive ? effectiveBuyPrice : maxPrice;

  const pricePerShare = isBuying ? effectiveMaxBuyPrice : minPrice;
  const totalCost = pricePerShare * quantity;
  const maxBuyable = Math.floor(balance / (effectiveMaxBuyPrice || 1));
  const maxSellable = meme.user_owns_shares || 0;

  // Fetch balance once when modal opens (avoid loops caused by updating user state).
  useEffect(() => {
    if (hasFetchedBalanceRef.current) return;
    hasFetchedBalanceRef.current = true;

    const fetchBalance = async () => {
      try {
        const data = await tradingService.getBalance();
        const newBalance = Number(data.balance);
        if (!Number.isFinite(newBalance)) return;

        setBalance((prevBalance) => (prevBalance === newBalance ? prevBalance : newBalance));
        updateUser((prevUser) => {
          if (!prevUser) return prevUser;
          const prev = Number(prevUser.wallet_balance);
          if (Number.isFinite(prev) && prev === newBalance) return prevUser;
          return { ...prevUser, wallet_balance: newBalance };
        });
      } catch (err) {
        console.error('Error fetching balance:', err);
        // keep existing balance if request fails
      } finally {
        setLoadingBalance(false);
      }
    };

    fetchBalance();
  }, [updateUser]);

  const handleQuantityChange = (value) => {
    const num = parseInt(value) || 0;
    if (num < 0) return;
    
    if (isBuying) {
      // Can't buy more than available shares or afford
      const max = isIpoActive ? Math.min(meme.available_shares, maxBuyable) : maxBuyable;
      setQuantity(Math.min(num, max));
    } else {
      // Can't sell more than owned
      setQuantity(Math.min(num, maxSellable));
    }
    
    setError(null);
  };

  const handleTrade = async () => {
    if (quantity <= 0) {
      setError('Please enter a valid quantity');
      return;
    }

    if (isBuying && totalCost > balance) {
      setError('Insufficient balance');
      return;
    }

    if (!isBuying && quantity > maxSellable) {
      setError('You don\'t own enough shares');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let result;
      if (isBuying) {
        if (!isIpoActive) {
          const p = Number(maxPrice);
          if (!Number.isFinite(p) || p <= 0) {
            setError('Please enter a valid maximum price');
            setLoading(false);
            return;
          }
          result = await tradingService.buyShares(meme.id, quantity, p);
        } else {
          result = await tradingService.buyShares(meme.id, quantity);
        }
      } else {
        const p = Number(minPrice);
        if (!Number.isFinite(p) || p <= 0) {
          setError('Please enter a valid minimum price');
          setLoading(false);
          return;
        }
        result = await tradingService.sellShares(meme.id, quantity, p);
      }

      setSuccess(result.message);
      const newBalance = Number(result.new_balance);
      if (Number.isFinite(newBalance)) {
        setBalance((prevBalance) => (prevBalance === newBalance ? prevBalance : newBalance));
        updateUser((prevUser) => {
          if (!prevUser) return prevUser;
          const prev = Number(prevUser.wallet_balance);
          if (Number.isFinite(prev) && prev === newBalance) return prevUser;
          return { ...prevUser, wallet_balance: newBalance };
        });
      }

      // Call onComplete after a short delay
      setTimeout(() => {
        onComplete(result);
      }, 1500);
    } catch (err) {
      console.error('Trade error:', err);
      setError(err.response?.data?.detail || 'Trade failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const priceChange = meme.price_change_percent_24h || 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="trade-modal-overlay" onClick={onClose}>
      <div className="trade-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <span className={`trade-type ${type}`}>
              {isBuying ? 'Buy' : 'Sell'}
            </span>
            <h2>${meme.ticker}</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Meme Info */}
        <div className="meme-summary">
          <img src={meme.image_url} alt={meme.name} />
          <div className="meme-details">
            <h3>{meme.name}</h3>
            <div className="price-info">
              <span className="current-price">${meme.current_price.toFixed(2)}</span>
              <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
                {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {Math.abs(priceChange).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Balance Info */}
        <div className="balance-info">
          <div className="info-row">
            <span>Your Balance:</span>
            <span className="value">
              {loadingBalance ? <Loader size={14} className="spinning" /> : `$${balance.toFixed(2)}`}
            </span>
          </div>
          {!isBuying && (
            <div className="info-row">
              <span>Shares Owned:</span>
              <span className="value">{maxSellable}</span>
            </div>
          )}
          <div className="info-row">
            <span>Available Shares:</span>
            <span className="value">{meme.available_shares.toLocaleString()}</span>
          </div>
        </div>

        {/* Quantity Input */}
        <div className="quantity-section">
          <label>Quantity</label>
          <div className="quantity-input">
            <button 
              onClick={() => handleQuantityChange(quantity - 1)}
              disabled={quantity <= 1}
            >
              <Minus size={18} />
            </button>
            <input
              type="number"
              value={quantity}
              onChange={(e) => handleQuantityChange(e.target.value)}
              min="1"
              max={isBuying ? (isIpoActive ? Math.min(meme.available_shares, maxBuyable) : maxBuyable) : maxSellable}
            />
            <button 
              onClick={() => handleQuantityChange(quantity + 1)}
              disabled={isBuying ? quantity >= (isIpoActive ? Math.min(meme.available_shares, maxBuyable) : maxBuyable) : quantity >= maxSellable}
            >
              <Plus size={18} />
            </button>
          </div>
          <div className="quick-amounts">
            {[10, 50, 100, 500].map(amt => (
              <button
                key={amt}
                onClick={() => handleQuantityChange(amt)}
                className={quantity === amt ? 'active' : ''}
              >
                {amt}
              </button>
            ))}
            <button 
              onClick={() => handleQuantityChange(isBuying ? maxBuyable : maxSellable)}
              className="max-btn"
            >
              MAX
            </button>
          </div>
        </div>

        {!isBuying && (
          <div className="quantity-section">
            <label>Minimum Price per Share</label>
            <div className="quantity-input">
              <input
                type="number"
                value={minPrice}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (!Number.isFinite(n)) return;
                  setMinPrice(n);
                  setError(null);
                }}
                min="0.01"
                step="0.01"
              />
            </div>
          </div>
        )}

        {isBuying && !isIpoActive && (
          <div className="quantity-section">
            <label>Maximum Price per Share</label>
            <div className="quantity-input">
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  if (!Number.isFinite(n)) return;
                  setMaxPrice(n);
                  setError(null);
                }}
                min="0.01"
                step="0.01"
              />
            </div>
          </div>
        )}

        {/* Order Summary */}
        <div className="order-summary">
          <div className="summary-row">
            <span>Price per Share:</span>
            <span>${Number(pricePerShare).toFixed(2)}</span>
          </div>
          <div className="summary-row">
            <span>Quantity:</span>
            <span>{quantity}</span>
          </div>
          <div className="summary-row total">
            <span>
              Total {isBuying ? (isIpoActive ? 'Cost' : 'Estimated Cost') : 'Value'}:
            </span>
            <span className={isBuying ? 'cost' : 'value'}>
              <DollarSign size={16} />
              {totalCost.toFixed(2)}
            </span>
          </div>
          {isBuying && (
            <div className="summary-row after">
              <span>Balance After:</span>
              <span>${(balance - totalCost).toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* Trade Notice */}
        <div className="price-impact">
          <AlertCircle size={14} />
          <span>
            {isBuying ? (
              isIpoActive
                ? <>IPO is active — buys fill at the fixed IPO price.</>
                : <>Post-IPO, buys place a buy order at your maximum price. It may fill immediately (often at lower ask prices) or remain pending until matched.</>
            ) : (
              <>This creates a sell listing at your minimum price; it may fill later when buyers match it.</>
            )}
          </span>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="message error">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="message success">
            <CheckCircle size={16} />
            <span>{success}</span>
          </div>
        )}

        {/* Action Button */}
        <button
          className={`trade-action-btn ${type}`}
          onClick={handleTrade}
          disabled={loading || quantity <= 0 || success}
        >
          {loading ? (
            <>
              <Loader size={18} className="spinning" />
              Processing...
            </>
          ) : success ? (
            <>
              <CheckCircle size={18} />
              Complete!
            </>
          ) : (
            <>
              <DollarSign size={18} />
              {isBuying ? 'Buy' : 'Sell'} {quantity} {quantity === 1 ? 'Share' : 'Shares'}
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default TradeModal;
