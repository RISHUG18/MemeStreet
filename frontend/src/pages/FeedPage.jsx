import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  TrendingUp, TrendingDown, Search, Filter, Grid, List,
  Flame, Sparkles, RefreshCw, ChevronDown
} from 'lucide-react';
import { memeService } from '../services/api';
import MemeCard from '../components/MemeCard';
import TradeModal from '../components/TradeModal';
import './FeedPage.css';

const CATEGORIES = [
  { value: '', label: 'All Categories' },
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

const SORT_OPTIONS = [
  { value: 'market_cap', label: 'Market Cap' },
  { value: 'price', label: 'Price' },
  { value: 'volume', label: '24h Volume' },
  { value: 'change', label: '24h Change' },
  { value: 'upvotes', label: 'Most Upvoted' },
  { value: 'newest', label: 'Newest' },
];

function FeedPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [memes, setMemes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  
  // Filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'market_cap');
  const [sortOrder, setSortOrder] = useState(searchParams.get('order') || 'desc');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  
  // Trade modal
  const [selectedMeme, setSelectedMeme] = useState(null);
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [tradeType, setTradeType] = useState('buy');

  // Fetch memes
  const fetchMemes = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        page,
        per_page: 12,
        sort_by: sortBy,
        sort_order: sortOrder,
      };
      
      if (category) params.category = category;
      if (searchQuery) params.search = searchQuery;
      
      const data = await memeService.getMemes(params);
      setMemes(data.memes);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (err) {
      console.error('Error fetching memes:', err);
      setError('Failed to load memes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch and refetch on filter change
  useEffect(() => {
    fetchMemes();
    
    // Update URL params
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (category) params.set('category', category);
    if (sortBy !== 'market_cap') params.set('sort', sortBy);
    if (sortOrder !== 'desc') params.set('order', sortOrder);
    setSearchParams(params);
  }, [page, category, sortBy, sortOrder]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        fetchMemes();
      } else {
        setPage(1); // Reset to page 1 on new search
      }
    }, 300);
    
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle meme interactions
  const handleUpvote = async (memeId) => {
    try {
      const result = await memeService.upvoteMeme(memeId);
      setMemes((prev) => prev.map((m) => {
        if (m.id !== memeId) return m;

        const wasUpvoted = !!m.user_has_upvoted;
        const wasDownvoted = !!m.user_has_downvoted;
        const nowUpvoted = !!result.success;

        let nextUpvotes = m.upvotes;
        let nextDownvotes = m.downvotes;

        if (wasUpvoted) {
          // toggled off
          nextUpvotes = Math.max(0, nextUpvotes - 1);
        } else {
          // added (possibly switching from downvote)
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
      setMemes((prev) => prev.map((m) => {
        if (m.id !== memeId) return m;

        const wasDownvoted = !!m.user_has_downvoted;
        const wasUpvoted = !!m.user_has_upvoted;
        const nowDownvoted = !!result.success;

        let nextDownvotes = m.downvotes;
        let nextUpvotes = m.upvotes;

        if (wasDownvoted) {
          // toggled off
          nextDownvotes = Math.max(0, nextDownvotes - 1);
        } else {
          // added (possibly switching from upvote)
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

  const handleTradeComplete = (updatedMeme) => {
    // Refresh memes after trade
    fetchMemes();
    setTradeModalOpen(false);
  };

  return (
    <div className="feed-page">
      {/* Header */}
      <div className="feed-header">
        <div className="feed-title">
          <h1>Meme Market</h1>
          <p>Trade the internet's hottest memes 📈</p>
        </div>
        
        <div className="feed-stats">
          <div className="stat-item">
            <Flame className="stat-icon hot" />
            <span>{total} Active Memes</span>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="filters-bar">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search memes by name or ticker..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <div className="filter-select">
            <Filter size={16} />
            <select 
              value={category} 
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
            <ChevronDown size={16} />
          </div>

          <div className="filter-select">
            <select 
              value={sortBy} 
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <ChevronDown size={16} />
          </div>

          <button 
            className={`sort-order-btn ${sortOrder}`}
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            title={sortOrder === 'desc' ? 'Descending' : 'Ascending'}
          >
            {sortOrder === 'desc' ? <TrendingDown size={18} /> : <TrendingUp size={18} />}
          </button>
        </div>

        <div className="view-toggle">
          <button 
            className={viewMode === 'grid' ? 'active' : ''} 
            onClick={() => setViewMode('grid')}
          >
            <Grid size={18} />
          </button>
          <button 
            className={viewMode === 'list' ? 'active' : ''} 
            onClick={() => setViewMode('list')}
          >
            <List size={18} />
          </button>
          <button className="refresh-btn" onClick={fetchMemes} disabled={loading}>
            <RefreshCw size={18} className={loading ? 'spinning' : ''} />
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={fetchMemes}>Try Again</button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-state">
          <div className="loader"></div>
          <p>Loading memes...</p>
        </div>
      )}

      {/* Meme Grid/List */}
      {!loading && !error && (
        <>
          {memes.length === 0 ? (
            <div className="empty-state">
              <Sparkles size={48} />
              <h3>No memes found</h3>
              <p>Try adjusting your filters or search query</p>
            </div>
          ) : (
            <div className={`memes-container ${viewMode}`}>
              {memes.map(meme => (
                <MemeCard
                  key={meme.id}
                  meme={meme}
                  viewMode={viewMode}
                  onUpvote={() => handleUpvote(meme.id)}
                  onDownvote={() => handleDownvote(meme.id)}
                  onBuy={() => handleTrade(meme, 'buy')}
                  onSell={() => handleTrade(meme, 'sell')}
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </button>
              
              <div className="page-info">
                Page {page} of {totalPages}
              </div>
              
              <button 
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
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

export default FeedPage;
