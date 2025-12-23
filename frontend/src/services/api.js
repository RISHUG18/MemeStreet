import axios from 'axios';

// API Base URL - will be environment variable in production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('memestreet_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      localStorage.removeItem('memestreet_token');
      localStorage.removeItem('memestreet_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============ AUTH SERVICES ============
export const authService = {
  /**
   * Login with email and password
   * 
   * How it works:
   * 1. Send email + password to backend
   * 2. Backend finds user by email
   * 3. Backend hashes input password and compares with stored hash
   * 4. If match -> returns JWT token + user data
   * 5. Frontend stores token for future requests
   */
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  /**
   * Register a new user
   * 
   * How it works:
   * 1. Send username, email, password to backend
   * 2. Backend validates data (email format, password length, etc.)
   * 3. Backend hashes password using bcrypt
   * 4. Backend stores user in MongoDB (with hashed password!)
   * 5. Returns success message
   */
  signup: async (username, email, password) => {
    const response = await api.post('/auth/signup', { username, email, password });
    return response.data;
  },

  /**
   * Get current user profile
   * 
   * Requires valid JWT token in header
   */
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Verify if token is still valid
   */
  verifyToken: async () => {
    const response = await api.post('/auth/verify-token');
    return response.data;
  }
};

// ============ MEME SERVICES ============
export const memeService = {
  getMemes: async (params = {}) => {
    const response = await api.get('/memes', { params });
    return response.data;
  },

  getMemeById: async (id) => {
    const response = await api.get(`/memes/${id}`);
    return response.data;
  },

  getMemeByTicker: async (ticker) => {
    const response = await api.get(`/memes/ticker/${ticker}`);
    return response.data;
  },

  getTrendingMemes: async (limit = 10) => {
    const response = await api.get('/memes/trending');
    return response.data;
  },

  getFeaturedMemes: async () => {
    const response = await api.get('/memes/featured');
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/memes/categories');
    return response.data;
  },

  createMeme: async (data) => {
    const response = await api.post('/memes', data);
    return response.data;
  },

  upvoteMeme: async (id) => {
    const response = await api.post(`/memes/${id}/upvote`);
    return response.data;
  },

  downvoteMeme: async (id) => {
    const response = await api.post(`/memes/${id}/downvote`);
    return response.data;
  },

  reportMeme: async (id) => {
    const response = await api.post(`/memes/${id}/report`);
    return response.data;
  },

  commentOnMeme: async (id, content) => {
    const response = await api.post(`/memes/${id}/comment?content=${encodeURIComponent(content)}`);
    return response.data;
  },

  getComments: async (id, page = 1, perPage = 20) => {
    const response = await api.get(`/memes/${id}/comments`, { params: { page, per_page: perPage } });
    return response.data;
  }
};

// ============ TRADING SERVICES ============
export const tradingService = {
  buyShares: async (memeId, quantity, maxPrice) => {
    const maxPricePart = (maxPrice !== undefined && maxPrice !== null)
      ? `&max_price=${encodeURIComponent(maxPrice)}`
      : '';
    const response = await api.post(`/trading/buy?meme_id=${memeId}&quantity=${quantity}${maxPricePart}`);
    return response.data;
  },

  sellShares: async (memeId, quantity, minPrice) => {
    const minPricePart = (minPrice !== undefined && minPrice !== null)
      ? `&min_price=${encodeURIComponent(minPrice)}`
      : '';
    const response = await api.post(`/trading/sell?meme_id=${memeId}&quantity=${quantity}${minPricePart}`);
    return response.data;
  },

  getTransactionHistory: async (params = {}) => {
    const response = await api.get('/trading/history', { params });
    return response.data;
  },

  getPortfolio: async () => {
    const response = await api.get('/trading/portfolio');
    return response.data;
  },

  cancelOrder: async (orderId) => {
    const response = await api.post(`/trading/orders/${orderId}/cancel`);
    return response.data;
  },

  getBalance: async () => {
    const response = await api.get('/trading/balance');
    return response.data;
  }
};

// ============ USER SERVICES ============
export const userService = {
  getLeaderboard: async (limit = 10) => {
    const response = await api.get('/users/leaderboard', { 
      params: { limit } 
    });
    return response.data;
  },

  getUserStats: async (userId) => {
    const response = await api.get(`/users/${userId}/stats`);
    return response.data;
  }
};

export default api;
