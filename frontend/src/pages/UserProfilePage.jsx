import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Camera, Upload, Plus, Image as ImageIcon, X, 
  TrendingUp, DollarSign, Users, Award, Edit2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { memeService, userService } from '../services/api';
import MemeCard from '../components/MemeCard';
import TradeModal from '../components/TradeModal';
import './UserProfilePage.css';

const CATEGORIES = [
  { value: 'crypto', label: '🪙 Crypto' },
  { value: 'stonks', label: '📈 Stonks' },
  { value: 'wojak', label: '😢 Wojak' },
  { value: 'pepe', label: '🐸 Pepe' },
  { value: 'anime', label: '🎌 Anime' },
  { value: 'gaming', label: '🎮 Gaming' },
  { value: 'politics', label: '🏛️ Politics' },
  { value: 'sports', label: '⚽ Sports' },
  { value: 'tech', label: '💻 Tech' },
  { value: 'other', label: '🌐 Other' },
];

function UserProfilePage() {
  const { userId } = useParams();
  const { user: currentUser, isAuthenticated } = useAuth();
  const isOwnProfile = !userId || userId === currentUser?.id;

  // State
  const [userProfile, setUserProfile] = useState(null);
  const [userMemes, setUserMemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('posted'); // 'posted' or 'portfolio'
  
  // Post meme modal
  const [showPostModal, setShowPostModal] = useState(false);
  const [postForm, setPostForm] = useState({
    name: '',
    ticker: '',
    description: '',
    category: 'other',
    image_url: '',
  });
  const [imagePreview, setImagePreview] = useState('');
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState('');

  // Trade modal
  const [selectedMeme, setSelectedMeme] = useState(null);
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [tradeType, setTradeType] = useState('buy');

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserProfile();
      fetchUserMemes();
    }
  }, [userId, isAuthenticated]);

  const fetchUserProfile = async () => {
    try {
      // For now, use current user data from context
      // In production, fetch user by userId
      setUserProfile(currentUser);
    } catch (err) {
      console.error('Error fetching user profile:', err);
    }
  };

  const fetchUserMemes = async () => {
    setLoading(true);
    try {
      // Fetch memes created by this user
      const data = await memeService.getMemes({ 
        page: 1, 
        per_page: 50,
        // In production, add creator_id filter
      });
      setUserMemes(data.memes || []);
    } catch (err) {
      console.error('Error fetching user memes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleImageChange = (e) => {
    const url = e.target.value;
    setPostForm({ ...postForm, image_url: url });
    setImagePreview(url);
  };

  const handlePostMeme = async (e) => {
    e.preventDefault();
    setPosting(true);
    setPostError('');

    try {
      // Validate ticker format (uppercase, 3-5 chars)
      const ticker = postForm.ticker.toUpperCase();
      if (!/^[A-Z]{3,5}$/.test(ticker)) {
        throw new Error('Ticker must be 3-5 uppercase letters');
      }

      const memeData = {
        name: postForm.name.trim(),
        ticker: ticker,
        description: postForm.description.trim(),
        category: postForm.category,
        image_url: postForm.image_url.trim(),
      };

      await memeService.createMeme(memeData);
      
      // Reset form and close modal
      setPostForm({
        name: '',
        ticker: '',
        description: '',
        category: 'other',
        image_url: '',
      });
      setImagePreview('');
      setShowPostModal(false);
      
      // Refresh memes
      fetchUserMemes();
    } catch (err) {
      console.error('Error posting meme:', err);
      setPostError(err.response?.data?.detail || err.message || 'Failed to post meme');
    } finally {
      setPosting(false);
    }
  };

  const handleUpvote = async (memeId) => {
    try {
      const result = await memeService.upvoteMeme(memeId);
      setUserMemes((prev) => prev.map((m) => {
        if (m.id !== memeId) return m;
        
        const wasUpvoted = !!m.user_has_upvoted;
        const wasDownvoted = !!m.user_has_downvoted;
        const nowUpvoted = !!result.success;

        let nextUpvotes = m.upvotes;
        let nextDownvotes = m.downvotes;

        if (wasUpvoted) {
          nextUpvotes = Math.max(0, nextUpvotes - 1);
        } else {
          nextUpvotes = nextUpvotes + 1;
          if (wasDownvoted) nextDownvotes = Math.max(0, nextDownvotes - 1);
        }

        return {
          ...m,
          current_price: result.new_price,
          user_has_upvoted: nowUpvoted,
          user_has_downvoted: false,
          upvotes: nextUpvotes,
          downvotes: nextDownvotes,
        };
      }));
    } catch (err) {
      console.error('Error upvoting:', err);
    }
  };

  const handleDownvote = async (memeId) => {
    try {
      const result = await memeService.downvoteMeme(memeId);
      setUserMemes((prev) => prev.map((m) => {
        if (m.id !== memeId) return m;

        const wasDownvoted = !!m.user_has_downvoted;
        const wasUpvoted = !!m.user_has_upvoted;
        const nowDownvoted = !!result.success;

        let nextDownvotes = m.downvotes;
        let nextUpvotes = m.upvotes;

        if (wasDownvoted) {
          nextDownvotes = Math.max(0, nextDownvotes - 1);
        } else {
          nextDownvotes = nextDownvotes + 1;
          if (wasUpvoted) nextUpvotes = Math.max(0, nextUpvotes - 1);
        }

        return {
          ...m,
          current_price: result.new_price,
          user_has_downvoted: nowDownvoted,
          user_has_upvoted: false,
          downvotes: nextDownvotes,
          upvotes: nextUpvotes,
        };
      }));
    } catch (err) {
      console.error('Error downvoting:', err);
    }
  };

  const handleTrade = (meme, type) => {
    setSelectedMeme(meme);
    setTradeType(type);
    setTradeModalOpen(true);
  };

  const handleTradeComplete = () => {
    fetchUserMemes();
    setTradeModalOpen(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="profile-page">
        <div className="profile-error">Please log in to view profiles</div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      {/* Profile Header */}
      <div className="profile-header">
        <div className="profile-info">
          <div className="profile-avatar">
            <Users size={48} />
          </div>
          <div className="profile-details">
            <h1 className="profile-username">{userProfile?.username || 'User'}</h1>
            <p className="profile-email">{userProfile?.email || ''}</p>
          </div>
        </div>

        <div className="profile-stats">
          <div className="stat-card">
            <DollarSign className="stat-icon" />
            <div className="stat-value">${(userProfile?.balance || 0).toFixed(2)}</div>
            <div className="stat-label">Balance</div>
          </div>
          <div className="stat-card">
            <TrendingUp className="stat-icon" />
            <div className="stat-value">${(userProfile?.portfolio_value || 0).toFixed(2)}</div>
            <div className="stat-label">Portfolio</div>
          </div>
          <div className="stat-card">
            <Award className="stat-icon" />
            <div className="stat-value">{userMemes.length}</div>
            <div className="stat-label">Memes Posted</div>
          </div>
        </div>

        {isOwnProfile && (
          <button 
            className="post-meme-btn"
            onClick={() => setShowPostModal(true)}
          >
            <Plus size={20} />
            Post New Meme
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="profile-tabs">
        <button 
          className={`tab ${activeTab === 'posted' ? 'active' : ''}`}
          onClick={() => setActiveTab('posted')}
        >
          Posted Memes
        </button>
        <button 
          className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setActiveTab('portfolio')}
        >
          Portfolio
        </button>
      </div>

      {/* Content */}
      <div className="profile-content">
        {activeTab === 'posted' && (
          <div className="memes-grid">
            {loading ? (
              <div className="loading-spinner"></div>
            ) : userMemes.length > 0 ? (
              userMemes.map(meme => (
                <MemeCard
                  key={meme.id}
                  meme={meme}
                  viewMode="card"
                  onUpvote={handleUpvote}
                  onDownvote={handleDownvote}
                  onBuy={(meme) => handleTrade(meme, 'buy')}
                  onSell={(meme) => handleTrade(meme, 'sell')}
                />
              ))
            ) : (
              <div className="empty-state">
                <ImageIcon size={48} />
                <p>No memes posted yet</p>
                {isOwnProfile && (
                  <button 
                    className="post-first-meme-btn"
                    onClick={() => setShowPostModal(true)}
                  >
                    Post your first meme
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'portfolio' && (
          <div className="portfolio-view">
            <p>Portfolio view coming soon...</p>
          </div>
        )}
      </div>

      {/* Post Meme Modal */}
      {showPostModal && (
        <div className="modal-overlay" onClick={() => setShowPostModal(false)}>
          <div className="post-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                <Upload size={24} />
                Post New Meme
              </h2>
              <button 
                className="close-btn"
                onClick={() => setShowPostModal(false)}
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handlePostMeme} className="post-form">
              {postError && (
                <div className="error-message">{postError}</div>
              )}

              <div className="form-group">
                <label>Meme Name *</label>
                <input
                  type="text"
                  value={postForm.name}
                  onChange={(e) => setPostForm({ ...postForm, name: e.target.value })}
                  placeholder="e.g., Doge to the Moon"
                  required
                  maxLength={100}
                />
              </div>

              <div className="form-group">
                <label>Ticker Symbol * (3-5 letters)</label>
                <input
                  type="text"
                  value={postForm.ticker}
                  onChange={(e) => setPostForm({ 
                    ...postForm, 
                    ticker: e.target.value.toUpperCase() 
                  })}
                  placeholder="e.g., DOGE"
                  required
                  maxLength={5}
                  pattern="[A-Za-z]{3,5}"
                />
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={postForm.description}
                  onChange={(e) => setPostForm({ ...postForm, description: e.target.value })}
                  placeholder="Describe your meme..."
                  required
                  maxLength={500}
                  rows={4}
                />
              </div>

              <div className="form-group">
                <label>Category *</label>
                <select
                  value={postForm.category}
                  onChange={(e) => setPostForm({ ...postForm, category: e.target.value })}
                  required
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Image URL *</label>
                <input
                  type="url"
                  value={postForm.image_url}
                  onChange={handleImageChange}
                  placeholder="https://example.com/meme.jpg"
                  required
                />
                {imagePreview && (
                  <div className="image-preview">
                    <img src={imagePreview} alt="Preview" onError={() => setImagePreview('')} />
                  </div>
                )}
              </div>

              <div className="form-actions">
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setShowPostModal(false)}
                  disabled={posting}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="submit-btn"
                  disabled={posting}
                >
                  {posting ? 'Posting...' : 'Post Meme'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Trade Modal */}
      {tradeModalOpen && selectedMeme && (
        <TradeModal
          meme={selectedMeme}
          type={tradeType}
          onClose={() => setTradeModalOpen(false)}
          onComplete={handleTradeComplete}
        />
      )}
    </div>
  );
}

export default UserProfilePage;
