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

  getTrendingMemes: async (limit = 10) => {
    const response = await api.get('/memes', { 
      params: { sort_by: 'trending', limit } 
    });
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

  commentOnMeme: async (id, content) => {
    const response = await api.post(`/memes/${id}/comments`, { content });
    return response.data;
  }
};

// ============ TRANSACTION SERVICES ============
export const transactionService = {
  buyMeme: async (memeId, quantity) => {
    const response = await api.post('/transactions/buy', { 
      meme_id: memeId, 
      quantity 
    });
    return response.data;
  },

  sellMeme: async (memeId, quantity) => {
    const response = await api.post('/transactions/sell', { 
      meme_id: memeId, 
      quantity 
    });
    return response.data;
  },

  getTransactionHistory: async (params = {}) => {
    const response = await api.get('/transactions', { params });
    return response.data;
  }
};

// ============ USER SERVICES ============
export const userService = {
  getPortfolio: async () => {
    const response = await api.get('/users/portfolio');
    return response.data;
  },

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
