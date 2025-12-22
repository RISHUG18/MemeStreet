import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Rocket, 
  Mail, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  ArrowRight,
  TrendingUp,
  Sparkles,
  AlertCircle,
  Check
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './AuthPage.css';

const AuthPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { login, signup, isLoading, error: authError } = useAuth();
  
  const isLoginMode = location.pathname === '/login';
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });

  const [touched, setTouched] = useState({
    username: false,
    email: false,
    password: false,
    confirmPassword: false
  });

  // Validation rules
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const validatePassword = (password) => {
    return password.length >= 8;
  };

  const validateUsername = (username) => {
    return username.length >= 3 && /^[a-zA-Z0-9_]+$/.test(username);
  };

  const getFieldError = (field) => {
    if (!touched[field]) return '';
    
    switch (field) {
      case 'email':
        if (!formData.email) return 'Email is required';
        if (!validateEmail(formData.email)) return 'Invalid email format';
        return '';
      case 'password':
        if (!formData.password) return 'Password is required';
        if (!validatePassword(formData.password)) return 'Password must be at least 8 characters';
        return '';
      case 'username':
        if (!formData.username) return 'Username is required';
        if (!validateUsername(formData.username)) return 'Username must be 3+ chars (letters, numbers, underscore)';
        return '';
      case 'confirmPassword':
        if (!formData.confirmPassword) return 'Please confirm your password';
        if (formData.password !== formData.confirmPassword) return 'Passwords do not match';
        return '';
      default:
        return '';
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setFormError('');
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched(prev => ({ ...prev, [name]: true }));
  };

  const isFormValid = () => {
    if (isLoginMode) {
      return validateEmail(formData.email) && formData.password.length > 0;
    }
    return (
      validateUsername(formData.username) &&
      validateEmail(formData.email) &&
      validatePassword(formData.password) &&
      formData.password === formData.confirmPassword
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');

    // Touch all fields to show validation
    setTouched({
      username: true,
      email: true,
      password: true,
      confirmPassword: true
    });

    if (!isFormValid()) {
      setFormError('Please fix the errors above');
      return;
    }

    try {
      if (isLoginMode) {
        await login(formData.email, formData.password);
        navigate('/dashboard');
      } else {
        await signup(formData.username, formData.email, formData.password);
        setFormSuccess('Account created! Redirecting to login...');
        setTimeout(() => {
          navigate('/login');
        }, 1500);
      }
    } catch (err) {
      setFormError(err.message || 'An error occurred');
    }
  };

  const switchMode = () => {
    setFormError('');
    setFormSuccess('');
    setTouched({
      username: false,
      email: false,
      password: false,
      confirmPassword: false
    });
    navigate(isLoginMode ? '/signup' : '/login');
  };

  return (
    <div className="auth-page">
      {/* Background Effects */}
      <div className="auth-bg">
        <div className="auth-grid"></div>
        <div className="auth-orb orb-1"></div>
        <div className="auth-orb orb-2"></div>
      </div>

      {/* Left Panel - Branding */}
      <div className="auth-branding">
        <div className="branding-content">
          <div className="branding-logo" onClick={() => navigate('/')}>
            <Rocket className="logo-icon" />
            <span className="logo-text">
              Meme<span className="gradient-text">Street</span>
            </span>
          </div>
          
          <h1 className="branding-title">
            {isLoginMode ? 'Welcome Back, Trader!' : 'Join the Meme Economy'}
          </h1>
          
          <p className="branding-subtitle">
            {isLoginMode 
              ? 'Your portfolio is waiting. Log in to continue trading memes.'
              : 'Create your account and start trading memes like stocks.'}
          </p>

          <div className="branding-features">
            <div className="feature-item">
              <div className="feature-icon">
                <TrendingUp size={20} />
              </div>
              <span>Real-time meme prices</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <Sparkles size={20} />
              </div>
              <span>100 free coins to start</span>
            </div>
          </div>

          <div className="branding-stats">
            <div className="stat">
              <span className="stat-value">50K+</span>
              <span className="stat-label">Traders</span>
            </div>
            <div className="stat">
              <span className="stat-value">10K+</span>
              <span className="stat-label">Memes</span>
            </div>
            <div className="stat">
              <span className="stat-value">$2.5M</span>
              <span className="stat-label">Daily Volume</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Form */}
      <div className="auth-form-container">
        <div className="auth-form-wrapper">
          <div className="auth-form-header">
            <h2 className="form-title">
              {isLoginMode ? 'Log In' : 'Create Account'}
            </h2>
            <p className="form-subtitle">
              {isLoginMode 
                ? 'Enter your credentials to access your account'
                : 'Fill in your details to get started'}
            </p>
          </div>

          {/* Error/Success Messages */}
          {(formError || authError) && (
            <div className="alert alert-error">
              <AlertCircle size={18} />
              <span>{formError || authError}</span>
            </div>
          )}
          
          {formSuccess && (
            <div className="alert alert-success">
              <Check size={18} />
              <span>{formSuccess}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {/* Username - Signup only */}
            {!isLoginMode && (
              <div className={`form-group ${getFieldError('username') ? 'error' : ''}`}>
                <label htmlFor="username">Username</label>
                <div className="input-wrapper">
                  <User className="input-icon" size={18} />
                  <input
                    type="text"
                    id="username"
                    name="username"
                    placeholder="Choose a username"
                    value={formData.username}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    autoComplete="username"
                  />
                </div>
                {getFieldError('username') && (
                  <span className="field-error">{getFieldError('username')}</span>
                )}
              </div>
            )}

            {/* Email */}
            <div className={`form-group ${getFieldError('email') ? 'error' : ''}`}>
              <label htmlFor="email">Email</label>
              <div className="input-wrapper">
                <Mail className="input-icon" size={18} />
                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete="email"
                />
              </div>
              {getFieldError('email') && (
                <span className="field-error">{getFieldError('email')}</span>
              )}
            </div>

            {/* Password */}
            <div className={`form-group ${getFieldError('password') ? 'error' : ''}`}>
              <label htmlFor="password">Password</label>
              <div className="input-wrapper">
                <Lock className="input-icon" size={18} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  placeholder={isLoginMode ? 'Enter your password' : 'Create a password (8+ chars)'}
                  value={formData.password}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  autoComplete={isLoginMode ? 'current-password' : 'new-password'}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {getFieldError('password') && (
                <span className="field-error">{getFieldError('password')}</span>
              )}
            </div>

            {/* Confirm Password - Signup only */}
            {!isLoginMode && (
              <div className={`form-group ${getFieldError('confirmPassword') ? 'error' : ''}`}>
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="input-wrapper">
                  <Lock className="input-icon" size={18} />
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    name="confirmPassword"
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
                {getFieldError('confirmPassword') && (
                  <span className="field-error">{getFieldError('confirmPassword')}</span>
                )}
              </div>
            )}

            {/* Forgot Password - Login only */}
            {isLoginMode && (
              <div className="form-options">
                <button type="button" className="forgot-password">
                  Forgot password?
                </button>
              </div>
            )}

            {/* Submit Button */}
            <button 
              type="submit" 
              className="btn-auth-submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="loading-spinner"></span>
              ) : (
                <>
                  {isLoginMode ? 'Log In' : 'Create Account'}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="auth-divider">
            <span>or continue with</span>
          </div>

          {/* Social Login */}
          <div className="social-login">
            <button type="button" className="btn-social btn-google">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Google
            </button>
            <button type="button" className="btn-social btn-github">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub
            </button>
          </div>

          {/* Switch Mode */}
          <div className="auth-switch">
            <span>
              {isLoginMode ? "Don't have an account?" : 'Already have an account?'}
            </span>
            <button type="button" onClick={switchMode}>
              {isLoginMode ? 'Sign up' : 'Log in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
