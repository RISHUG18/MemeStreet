import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Play, Sparkles, TrendingUp, Users, Zap } from 'lucide-react';
import './Hero.css';

const Hero = () => {
  const navigate = useNavigate();

  return (
    <section className="hero">
      {/* Background Elements */}
      <div className="hero-bg">
        <div className="grid-overlay"></div>
        <div className="glow-orb orb-1"></div>
        <div className="glow-orb orb-2"></div>
        <div className="glow-orb orb-3"></div>
      </div>

      <div className="hero-container">
        <div className="hero-content">
          {/* Badge */}
          <div className="hero-badge">
            <Sparkles size={14} />
            <span>Welcome to the Meme Economy</span>
          </div>

          {/* Main Heading */}
          <h1 className="hero-title">
            The <span className="gradient-text">Wall Street</span> of
            <br />
            Internet Culture
          </h1>

          {/* Subtitle */}
          <p className="hero-subtitle">
            Trade memes like stocks. Watch prices soar with viral content.
            Build your portfolio, climb the leaderboard, and become a meme mogul.
          </p>

          {/* CTA Buttons */}
          <div className="hero-cta">
            <button className="btn btn-hero-primary" onClick={() => navigate('/feed')}>
              Start Trading Free
              <ArrowRight size={18} />
            </button>
            <button className="btn btn-hero-secondary" onClick={() => navigate('/feed')}>
              <Play size={18} />
              Browse Memes
            </button>
          </div>

          {/* Stats */}
          <div className="hero-stats">
            <div className="stat-item">
              <div className="stat-icon">
                <Users size={20} />
              </div>
              <div className="stat-info">
                <span className="stat-value">50K+</span>
                <span className="stat-label">Active Traders</span>
              </div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-icon">
                <TrendingUp size={20} />
              </div>
              <div className="stat-info">
                <span className="stat-value">$2.5M</span>
                <span className="stat-label">Daily Volume</span>
              </div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-icon">
                <Zap size={20} />
              </div>
              <div className="stat-info">
                <span className="stat-value">10K+</span>
                <span className="stat-label">Memes Listed</span>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Visual */}
        <div className="hero-visual">
          <div className="trading-card-stack">
            {/* Meme Cards */}
            <div className="meme-card card-1">
              <div className="meme-card-header">
                <span className="meme-ticker">$DOGE</span>
                <span className="meme-change positive">+24.5%</span>
              </div>
              <div className="meme-card-image">
                <span className="meme-emoji">🐕</span>
              </div>
              <div className="meme-card-footer">
                <span className="meme-price">420.69</span>
                <span className="meme-label">coins</span>
              </div>
            </div>

            <div className="meme-card card-2">
              <div className="meme-card-header">
                <span className="meme-ticker">$STONKS</span>
                <span className="meme-change positive">+156%</span>
              </div>
              <div className="meme-card-image">
                <span className="meme-emoji">📈</span>
              </div>
              <div className="meme-card-footer">
                <span className="meme-price">999.99</span>
                <span className="meme-label">coins</span>
              </div>
            </div>

            <div className="meme-card card-3">
              <div className="meme-card-header">
                <span className="meme-ticker">$PEPE</span>
                <span className="meme-change negative">-3.2%</span>
              </div>
              <div className="meme-card-image">
                <span className="meme-emoji">🐸</span>
              </div>
              <div className="meme-card-footer">
                <span className="meme-price">156.32</span>
                <span className="meme-label">coins</span>
              </div>
            </div>
          </div>

          {/* Floating Elements */}
          <div className="floating-badge badge-1">
            <TrendingUp size={16} className="badge-icon" />
            <span>+420% today</span>
          </div>
          <div className="floating-badge badge-2">
            <Sparkles size={16} className="badge-icon" />
            <span>Trending</span>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="scroll-indicator">
        <div className="scroll-mouse">
          <div className="scroll-wheel"></div>
        </div>
        <span>Scroll to explore</span>
      </div>
    </section>
  );
};

export default Hero;
