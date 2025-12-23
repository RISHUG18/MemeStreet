import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Filter, Loader } from 'lucide-react';
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
  { value: 'newest', label: 'Newest' },
  { value: 'upvotes', label: 'Most Upvoted' },
  { value: 'market_cap', label: 'Market Cap' },
  { value: 'price', label: 'Price' },
  { value: 'volume', label: '24h Volume' },
  { value: 'change', label: '24h Change' },
];

function FeedPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [memes, setMemes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'newest');
  
  // Infinite scroll
  const [page, setPage] = useState(1);
  const observer = useRef();
  const lastMemeRef = useCallback(node => {
    if (loading) return;
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        setPage(prevPage => prevPage + 1);
      }
    });
    if (node) observer.current.observe(node);
  }, [loading, hasMore]);
  
  // Trade modal
  const [selectedMeme, setSelectedMeme] = useState(null);
  const [tradeModalOpen, setTradeModalOpen] = useState(false);
  const [tradeType, setTradeType] = useState('buy');

  // Fetch memes
  const fetchMemes = async (resetPage = false) => {
    if (!hasMore && !resetPage) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        page: resetPage ? 1 : page,
        per_page: 10,
        sort_by: sortBy,
        sort_order: 'desc',
      };
      
      if (category) params.category = category;
      if (searchQuery) params.search = searchQuery;
      
      const data = await memeService.getMemes(params);
      
      if (resetPage) {
        setMemes(data.memes);
        setPage(1);
      } else {
        setMemes(prevMemes => [...prevMemes, ...data.memes]);
      }
      
      setHasMore(data.memes.length === 10);
    } catch (err) {
      console.error('Error fetching memes:', err);
      setError('Failed to load memes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch more memes when page changes
  useEffect(() => {
    if (page > 1) {
      fetchMemes();
    }
  }, [page]);

  // Reset and fetch on filter change
  useEffect(() => {
    setMemes([]);
    setPage(1);
    setHasMore(true);
    fetchMemes(true);
    
    // Update URL params
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (category) params.set('category', category);
    if (sortBy !== 'newest') params.set('sort', sortBy);
    setSearchParams(params);
  }, [category, sortBy]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      setMemes([]);
      setPage(1);
      setHasMore(true);
      fetchMemes(true);
    }, 500);
    
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
      setMemes((prev) => prev.map((m) => {
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

  const handleMemeClick = (meme) => {
    setSelectedMeme(meme);
    setTradeType('buy');
    setTradeModalOpen(true);
  };

  const handleTradeComplete = (updatedMeme) => {
    setMemes(prevMemes => prevMemes.map(m => 
      m.id === updatedMeme?.id ? { ...m, ...updatedMeme } : m
    ));
    setTradeModalOpen(false);
  };

  return (
    <div className="feed-page instagram-style">
      {/* Sticky Header */}
      <div className="feed-sticky-header">
        <h1 className="feed-logo">MemeStreet</h1>
        
        <div className="header-filters">
          <div className="search-box-small">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-select-small">
            <Filter size={16} />
            <select 
              value={category} 
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-select-small">
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value)}
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Scrollable Feed */}
      <div className="instagram-feed">
        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        {memes.map((meme, index) => {
          if (memes.length === index + 1) {
            return (
              <div key={meme.id} ref={lastMemeRef}>
                <MemeCard
                  meme={meme}
                  viewMode="instagram"
                  onUpvote={handleUpvote}
                  onDownvote={handleDownvote}
                  onMemeClick={handleMemeClick}
                />
              </div>
            );
          } else {
            return (
              <MemeCard
                key={meme.id}
                meme={meme}
                viewMode="instagram"
                onUpvote={handleUpvote}
                onDownvote={handleDownvote}
                onMemeClick={handleMemeClick}
              />
            );
          }
        })}

        {loading && (
          <div className="loading-indicator">
            <Loader className="spinner" size={32} />
            <p>Loading memes...</p>
          </div>
        )}

        {!loading && memes.length === 0 && (
          <div className="empty-feed">
            <p>No memes found. Try adjusting your filters.</p>
          </div>
        )}

        {!hasMore && memes.length > 0 && (
          <div className="end-of-feed">
            <p>You've reached the end! 🎉</p>
          </div>
        )}
      </div>

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
