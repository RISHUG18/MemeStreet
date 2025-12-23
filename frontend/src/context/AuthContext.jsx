import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('memestreet_token');
      const savedUser = localStorage.getItem('memestreet_user');
      
      if (token && savedUser) {
        try {
          // Validate token with backend (optional - for now just restore from localStorage)
          setUser(JSON.parse(savedUser));
        } catch (err) {
          // Token invalid, clear storage
          localStorage.removeItem('memestreet_token');
          localStorage.removeItem('memestreet_user');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await authService.login(email, password);
      
      // Store token and user data
      localStorage.setItem('memestreet_token', response.access_token);
      localStorage.setItem('memestreet_user', JSON.stringify(response.user));
      
      setUser(response.user);
      return response;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (username, email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await authService.signup(username, email, password);
      return response;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Signup failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('memestreet_token');
    localStorage.removeItem('memestreet_user');
    setUser(null);
  };

  // Update cached user without forcing consumers to re-create callbacks.
  // Supports either a partial object OR a functional updater.
  const updateUser = useCallback((update) => {
    setUser((prev) => {
      const next = typeof update === 'function'
        ? update(prev)
        : (prev ? { ...prev, ...update } : update);

      if (next) {
        localStorage.setItem('memestreet_user', JSON.stringify(next));
      } else {
        localStorage.removeItem('memestreet_user');
      }

      return next;
    });
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const value = useMemo(() => ({
    user,
    isLoading,
    error,
    isAuthenticated: !!user,
    login,
    signup,
    logout,
    updateUser,
    clearError,
  }), [user, isLoading, error, login, signup, logout, updateUser, clearError]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
