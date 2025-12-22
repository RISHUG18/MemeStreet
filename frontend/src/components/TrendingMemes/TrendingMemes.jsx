import React from 'react';
import { TrendingUp, TrendingDown, Flame } from 'lucide-react';
import './TrendingMemes.css';

const trendingMemes = [
  {
    id: 1,
    ticker: 'DOGE',
    name: 'Doge to the Moon',
    emoji: '🐕',
    price: 420.69,
    change: 24.5,
    volume: '12.5K',
    holders: 2847,
    trending: true
  },
  {
    id: 2,
    ticker: 'STONKS',
    name: 'Stonks Only Go Up',
    emoji: '📈',
    price: 999.99,
    change: 156.2,
    volume: '45.2K',
    holders: 5621,
    trending: true
  },
  {
    id: 3,
    ticker: 'PEPE',
    name: 'Rare Pepe Collection',
    emoji: '🐸',
    price: 156.32,
    change: -3.2,
    volume: '8.9K',
    holders: 1923,
    trending: false
  },
  {
    id: 4,
    ticker: 'CHAD',
    name: 'Yes Chad',
    emoji: '💪',
    price: 234.50,
    change: 15.3,
    volume: '6.7K',
    holders: 1456,
    trending: true
  },
  {
    id: 5,
    ticker: 'WOJAK',
    name: 'Feels Bad Man',
    emoji: '😢',
    price: 89.99,
    change: 8.7,
    volume: '4.3K',
    holders: 987,
    trending: false
  },
  {
    id: 6,
    ticker: 'MOON',
    name: 'To The Moon',
    emoji: '🌙',
    price: 567.89,
    change: 42.1,
    volume: '23.1K',
    holders: 3254,
    trending: true
  }
];

const TrendingMemes = () => {
  return (
    <section id="trending" className="trending-section">
      <div className="trending-container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">
            <Flame size={14} />
            Live Market
          </span>
          <h2 className="section-title">
            <span className="gradient-text">Trending</span> Right Now
          </h2>
          <p className="section-subtitle">
            The hottest memes on the market. Prices update in real-time.
          </p>
        </div>

        {/* Meme Table */}
        <div className="meme-table-container">
          <table className="meme-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Meme</th>
                <th>Price</th>
                <th>24h Change</th>
                <th>Volume</th>
                <th>Holders</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {trendingMemes.map((meme, index) => (
                <tr key={meme.id}>
                  <td className="rank-cell">
                    {meme.trending && <Flame size={14} className="fire-icon" />}
                    {index + 1}
                  </td>
                  <td className="meme-cell">
                    <div className="meme-info">
                      <span className="meme-emoji-small">{meme.emoji}</span>
                      <div className="meme-details">
                        <span className="meme-ticker-name">${meme.ticker}</span>
                        <span className="meme-full-name">{meme.name}</span>
                      </div>
                    </div>
                  </td>
                  <td className="price-cell">
                    <span className="price-value">{meme.price.toFixed(2)}</span>
                    <span className="price-label">coins</span>
                  </td>
                  <td className={`change-cell ${meme.change >= 0 ? 'positive' : 'negative'}`}>
                    {meme.change >= 0 ? (
                      <TrendingUp size={16} />
                    ) : (
                      <TrendingDown size={16} />
                    )}
                    <span>{meme.change >= 0 ? '+' : ''}{meme.change}%</span>
                  </td>
                  <td className="volume-cell">{meme.volume}</td>
                  <td className="holders-cell">{meme.holders.toLocaleString()}</td>
                  <td className="action-cell">
                    <button className="btn-trade">Trade</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* View All */}
        <div className="view-all-container">
          <button className="btn-view-all">
            View All Memes
          </button>
        </div>
      </div>
    </section>
  );
};

export default TrendingMemes;
