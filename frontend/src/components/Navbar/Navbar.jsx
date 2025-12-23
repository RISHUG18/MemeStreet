import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Menu, X, Rocket, User, Wallet, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const walletBalance = (() => {
    const n = Number(user?.wallet_balance);
    return Number.isFinite(n) ? n : null;
  })();

  const handleLogout = () => {
    logout();
    setIsUserMenuOpen(false);
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <Rocket className="brand-icon" />
          <span className="brand-text">
            Meme<span className="brand-highlight">Street</span>
          </span>
        </Link>

        <div className={`navbar-links ${isMenuOpen ? 'active' : ''}`}>
          <Link to="/feed" className="nav-link nav-link-primary">Trade Memes</Link>
          {isAuthenticated && (
            <Link to="/portfolio" className="nav-link">Portfolio</Link>
          )}
          <a href="/#features" className="nav-link">Features</a>
          <a href="/#how-it-works" className="nav-link">How It Works</a>
          <a href="/#trending" className="nav-link">Trending</a>
          <a href="/#leaderboard" className="nav-link">Leaderboard</a>
        </div>

        {isAuthenticated ? (
          <div className="navbar-user">
            {/* Wallet Balance */}
            <div className="wallet-display">
              <Wallet size={16} />
              <span className="wallet-balance">
                {walletBalance !== null ? walletBalance.toFixed(2) : '0.00'}
              </span>
              <span className="wallet-label">coins</span>
            </div>

            {/* User Menu */}
            <div className="user-menu-wrapper">
              <button 
                className="user-menu-trigger"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              >
                <div className="user-avatar">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className="user-name">{user?.username || 'User'}</span>
                <ChevronDown size={16} className={isUserMenuOpen ? 'rotated' : ''} />
              </button>

              {isUserMenuOpen && (
                <div className="user-dropdown">
                  <Link 
                    to="/profile" 
                    className="dropdown-item"
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    <User size={16} />
                    My Profile
                  </Link>
                  <Link 
                    to="/portfolio" 
                    className="dropdown-item"
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    <Wallet size={16} />
                    Portfolio
                  </Link>
                  <div className="dropdown-divider"></div>
                  <button className="dropdown-item logout" onClick={handleLogout}>
                    <LogOut size={16} />
                    Log Out
                  </button>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="navbar-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => navigate('/login')}
            >
              Log In
            </button>
            <button 
              className="btn btn-primary"
              onClick={() => navigate('/signup')}
            >
              Start Trading
              <span className="btn-glow"></span>
            </button>
          </div>
        )}

        <button 
          className="mobile-menu-btn"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
