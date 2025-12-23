import React, { useState, useEffect } from 'react';
import { tradingService } from '../services/api';
import './PortfolioPage.css';

const PortfolioPage = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    try {
      const data = await tradingService.getPortfolio();
      setPortfolio(data);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
      setError('Failed to load portfolio');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    
    try {
      await tradingService.cancelOrder(orderId);
      // Refresh portfolio to remove the cancelled order and update balance/holdings
      fetchPortfolio();
    } catch (err) {
      console.error('Error cancelling order:', err);
      alert('Failed to cancel order');
    }
  };

  if (loading) return <div className="loading">Loading portfolio...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!portfolio) return null;

  // Map backend field names to what we use in the UI
  const cashBalance = portfolio.wallet_balance || 0;
  const portfolioValue = portfolio.portfolio_value || 0;
  const totalValue = cashBalance + portfolioValue;
  const totalPnl = portfolio.total_profit_loss || 0;
  const totalPnlPercent = portfolio.total_profit_loss_percent || 0;

  return (
    <div className="portfolio-page">
      <div className="portfolio-header">
        <h1>My Portfolio</h1>
      </div>

      <div className="portfolio-summary">
        <div className="summary-card">
          <h3>Cash Balance</h3>
          <div className="value">${cashBalance.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <h3>Total Portfolio Value</h3>
          <div className="value">${totalValue.toFixed(2)}</div>
          <div className={`sub-value ${totalPnl >= 0 ? 'positive' : 'negative'}`}>
            {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)} ({totalPnlPercent.toFixed(2)}%)
          </div>
        </div>
      </div>

      <h2 className="section-title">Holdings</h2>
      {portfolio.holdings.length === 0 ? (
        <div className="empty-state">No holdings yet</div>
      ) : (
        <div className="holdings-grid">
          {portfolio.holdings.map((holding) => (
            <div key={holding.meme_id} className="holding-card">
              <div className="holding-header">
                <h3>{holding.meme_name}</h3>
                <span className="ticker">{holding.meme_ticker}</span>
              </div>
              <div className="holding-stats">
                <div className="stat-row">
                  <label>Shares</label>
                  <span>{holding.quantity}</span>
                </div>
                <div className="stat-row">
                  <label>Avg Cost</label>
                  <span>${(holding.average_buy_price || 0).toFixed(2)}</span>
                </div>
                <div className="stat-row">
                  <label>Current Price</label>
                  <span>${(holding.current_price || 0).toFixed(2)}</span>
                </div>
                <div className="stat-row">
                  <label>Value</label>
                  <span>${(holding.current_value || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <h2 className="section-title">Open Orders</h2>
      {(!portfolio.open_orders || portfolio.open_orders.length === 0) ? (
        <div className="empty-state">No open orders</div>
      ) : (
        <div className="orders-list">
          {portfolio.open_orders.map((order) => (
            <div key={order.id} className="order-item">
              <div className="order-info">
                <div className={`order-type ${order.type}`}>
                  {order.type}
                </div>
                <div className="order-details">
                  <strong>{order.meme_ticker}</strong>
                  <span>{order.quantity} shares @ ${(order.price || 0).toFixed(2)}</span>
                </div>
              </div>
              <button 
                className="cancel-btn"
                onClick={() => handleCancelOrder(order.id)}
              >
                Cancel Order
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PortfolioPage;
