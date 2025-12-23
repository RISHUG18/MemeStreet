import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, ThumbsUp, ThumbsDown, 
  MessageCircle, Flag, Share2, ShoppingCart, DollarSign,
  Flame, Snowflake, Zap, Activity
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './MemeCard.css';

const getTrendIcon = (trend) => {
  switch (trend) {
    case 'hot': return <Flame className="trend-icon hot" />;
    case 'cold': return <Snowflake className="trend-icon cold" />;
    case 'volatile': return <Zap className="trend-icon volatile" />;
    default: return <Activity className="trend-icon stable" />;
  }
};

const formatNumber = (num) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toLocaleString();
};

const formatPrice = (price) => {
  if (price >= 1000) return '$' + formatNumber(price);
  if (price >= 1) return '$' + price.toFixed(2);
  return '$' + price.toFixed(4);
};

function MemeCard({ meme, viewMode, onUpvote, onDownvote, onBuy, onSell }) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const ipoEndAt = meme?.ipo_end_at ? new Date(meme.ipo_end_at) : null;
  const ipoSharesRemaining = Number(meme?.ipo_shares_remaining);
  const hasIpoTime = ipoEndAt instanceof Date && !Number.isNaN(ipoEndAt.getTime());
  const isIpoActive = !!(hasIpoTime && ipoEndAt.getTime() > Date.now() && (Number.isFinite(ipoSharesRemaining) ? ipoSharesRemaining > 0 : true));

  const priceChangePercent = meme.price_change_percent_24h || 0;
  const isPositive = priceChangePercent >= 0;

  const handleCardClick = (e) => {
    // Don't navigate if clicking on buttons
    if (e.target.closest('button')) return;
    navigate(`/meme/${meme.id}`);
  };

  const handleAction = (action, e) => {
    e.stopPropagation();
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    action();
  };

  if (viewMode === 'list') {
    return (
      <div className="meme-card list-view" onClick={handleCardClick}>
        <div className="meme-image-container small">
          {!imageLoaded && !imageError && <div className="image-skeleton"></div>}
          <img 
            src={imageError ? '/placeholder-meme.png' : meme.image_url} 
            alt={meme.name}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
            style={{ opacity: imageLoaded ? 1 : 0 }}
          />
        </div>

        <div className="meme-info">
          <div className="meme-header">
            <span className="meme-ticker">${meme.ticker}</span>
            <h3 className="meme-name">{meme.name}</h3>
            {getTrendIcon(meme.trend_status)}
          </div>
          <p className="meme-category">{meme.category}</p>
        </div>

        <div className="meme-price-section">
          <div className="current-price">{formatPrice(meme.current_price)}</div>
          <div className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {Math.abs(priceChangePercent).toFixed(2)}%
          </div>
        </div>

        <div className="meme-stats-row">
          <div className="stat">
            <ThumbsUp size={14} />
            <span>{formatNumber(meme.upvotes)}</span>
          </div>
          <div className="stat">
            <MessageCircle size={14} />
            <span>{formatNumber(meme.comments_count)}</span>
          </div>
          <div className="stat">
            <span>Vol: {formatNumber(meme.volume_24h)}</span>
          </div>
        </div>

        <div className="meme-actions-row">
          <button 
            className={`action-btn upvote ${meme.user_has_upvoted ? 'active' : ''}`}
            onClick={(e) => handleAction(onUpvote, e)}
          >
            <ThumbsUp size={16} />
          </button>
          <button 
            className={`action-btn downvote ${meme.user_has_downvoted ? 'active' : ''}`}
            onClick={(e) => handleAction(onDownvote, e)}
          >
            <ThumbsDown size={16} />
          </button>
          <button 
            className="trade-btn buy"
            onClick={(e) => handleAction(onBuy, e)}
          >
            Buy
          </button>
          {meme.user_owns_shares > 0 && !isIpoActive && (
            <button 
              className="trade-btn sell"
              onClick={(e) => handleAction(onSell, e)}
            >
              Sell
            </button>
          )}
        </div>
      </div>
    );
  }

  // Grid View (default)
  return (
    <div className="meme-card" onClick={handleCardClick}>
      {/* Image */}
      <div className="meme-image-container">
        {meme.is_featured && <div className="featured-badge">⭐ Featured</div>}
        {!imageLoaded && !imageError && <div className="image-skeleton"></div>}
        <img 
          src={imageError ? '/placeholder-meme.png' : meme.image_url} 
          alt={meme.name}
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageError(true)}
          style={{ opacity: imageLoaded ? 1 : 0 }}
        />
        <div className="meme-overlay">
          <div className="trend-badge">
            {getTrendIcon(meme.trend_status)}
            <span>{meme.trend_status}</span>
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="meme-content">
        <div className="meme-header">
          <div className="meme-title">
            <span className="meme-ticker">${meme.ticker}</span>
            <h3 className="meme-name">{meme.name}</h3>
          </div>
          <span className="meme-category">{meme.category}</span>
        </div>

        {/* Price */}
        <div className="meme-price">
          <div className="price-main">
            <span className="current-price">{formatPrice(meme.current_price)}</span>
            <span className={`price-change ${isPositive ? 'positive' : 'negative'}`}>
              {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {Math.abs(priceChangePercent).toFixed(2)}%
            </span>
          </div>
          <div className="price-details">
            <span>MCap: {formatPrice(meme.market_cap)}</span>
            <span>Vol: {formatNumber(meme.volume_24h)}</span>
          </div>
        </div>

        {/* Stats */}
        <div className="meme-stats">
          <div className="stat-item">
            <ThumbsUp size={14} />
            <span>{formatNumber(meme.upvotes)}</span>
          </div>
          <div className="stat-item">
            <ThumbsDown size={14} />
            <span>{formatNumber(meme.downvotes)}</span>
          </div>
          <div className="stat-item">
            <MessageCircle size={14} />
            <span>{formatNumber(meme.comments_count)}</span>
          </div>
        </div>

        {/* User's position */}
        {meme.user_owns_shares > 0 && (
          <div className="user-position">
            <ShoppingCart size={14} />
            <span>You own {formatNumber(meme.user_owns_shares)} shares</span>
          </div>
        )}

        {/* Actions */}
        <div className="meme-actions">
          <div className="vote-buttons">
            <button 
              className={`vote-btn upvote ${meme.user_has_upvoted ? 'active' : ''}`}
              onClick={(e) => handleAction(onUpvote, e)}
              title="Upvote (+0.5% price)"
            >
              <ThumbsUp size={18} />
            </button>
            <button 
              className={`vote-btn downvote ${meme.user_has_downvoted ? 'active' : ''}`}
              onClick={(e) => handleAction(onDownvote, e)}
              title="Downvote (-0.3% price)"
            >
              <ThumbsDown size={18} />
            </button>
          </div>
          
          <div className="trade-buttons">
            <button 
              className="trade-btn buy"
              onClick={(e) => handleAction(onBuy, e)}
            >
              <DollarSign size={16} />
              Buy
            </button>
            {meme.user_owns_shares > 0 && !isIpoActive && (
              <button 
                className="trade-btn sell"
                onClick={(e) => handleAction(onSell, e)}
              >
                Sell
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MemeCard;
