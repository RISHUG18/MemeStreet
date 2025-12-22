import React from 'react';
import { Trophy, Medal, Award, Crown, TrendingUp } from 'lucide-react';
import './Leaderboard.css';

const leaderboardData = [
  {
    rank: 1,
    username: 'MemeKing420',
    avatar: '👑',
    portfolio: 125420.69,
    gain: 1154.2,
    trades: 892,
    streetCred: 9850
  },
  {
    rank: 2,
    username: 'DiamondHands',
    avatar: '💎',
    portfolio: 98750.00,
    gain: 887.5,
    trades: 654,
    streetCred: 8420
  },
  {
    rank: 3,
    username: 'StonksGuru',
    avatar: '📈',
    portfolio: 87340.50,
    gain: 773.4,
    trades: 721,
    streetCred: 7890
  },
  {
    rank: 4,
    username: 'PepeWhisperer',
    avatar: '🐸',
    portfolio: 76890.25,
    gain: 668.9,
    trades: 543,
    streetCred: 6540
  },
  {
    rank: 5,
    username: 'ToTheMoon',
    avatar: '🚀',
    portfolio: 65420.00,
    gain: 554.2,
    trades: 432,
    streetCred: 5670
  }
];

const getRankIcon = (rank) => {
  switch (rank) {
    case 1:
      return <Crown className="rank-icon gold" />;
    case 2:
      return <Medal className="rank-icon silver" />;
    case 3:
      return <Award className="rank-icon bronze" />;
    default:
      return <span className="rank-number">{rank}</span>;
  }
};

const Leaderboard = () => {
  return (
    <section id="leaderboard" className="leaderboard-section">
      <div className="leaderboard-container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">
            <Trophy size={14} />
            Leaderboard
          </span>
          <h2 className="section-title">
            Top <span className="gradient-text">Meme Traders</span>
          </h2>
          <p className="section-subtitle">
            The elite traders dominating the meme market. Will you join them?
          </p>
        </div>

        {/* Leaderboard Cards */}
        <div className="leaderboard-grid">
          {/* Top 3 Podium */}
          <div className="podium">
            {leaderboardData.slice(0, 3).map((trader, index) => (
              <div 
                key={trader.rank} 
                className={`podium-card podium-${trader.rank}`}
              >
                <div className="podium-rank">
                  {getRankIcon(trader.rank)}
                </div>
                <div className="podium-avatar">{trader.avatar}</div>
                <h3 className="podium-username">{trader.username}</h3>
                <div className="podium-portfolio">
                  <span className="portfolio-value">
                    {trader.portfolio.toLocaleString()}
                  </span>
                  <span className="portfolio-label">coins</span>
                </div>
                <div className="podium-gain">
                  <TrendingUp size={14} />
                  <span>+{trader.gain}%</span>
                </div>
                <div className="podium-stats">
                  <div className="stat">
                    <span className="stat-value">{trader.trades}</span>
                    <span className="stat-label">Trades</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{trader.streetCred.toLocaleString()}</span>
                    <span className="stat-label">Street Cred</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Rest of Leaderboard */}
          <div className="leaderboard-list">
            {leaderboardData.slice(3).map((trader) => (
              <div key={trader.rank} className="leaderboard-row">
                <div className="row-rank">{getRankIcon(trader.rank)}</div>
                <div className="row-user">
                  <span className="row-avatar">{trader.avatar}</span>
                  <span className="row-username">{trader.username}</span>
                </div>
                <div className="row-portfolio">
                  <span className="row-value">{trader.portfolio.toLocaleString()}</span>
                  <span className="row-label">coins</span>
                </div>
                <div className="row-gain positive">
                  <TrendingUp size={14} />
                  <span>+{trader.gain}%</span>
                </div>
                <div className="row-cred">{trader.streetCred.toLocaleString()} SC</div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="leaderboard-cta">
          <p className="cta-text">Think you can make it to the top?</p>
          <button className="btn btn-leaderboard-primary">
            Start Your Journey
          </button>
        </div>
      </div>
    </section>
  );
};

export default Leaderboard;
