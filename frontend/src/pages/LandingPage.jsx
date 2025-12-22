import React from 'react';
import Navbar from '../components/Navbar/Navbar';
import StockTicker from '../components/StockTicker/StockTicker';
import Hero from '../components/Hero/Hero';
import Features from '../components/Features/Features';
import HowItWorks from '../components/HowItWorks/HowItWorks';
import TrendingMemes from '../components/TrendingMemes/TrendingMemes';
import Leaderboard from '../components/Leaderboard/Leaderboard';
import Footer from '../components/Footer/Footer';
import './LandingPage.css';

const LandingPage = () => {
  return (
    <div className="landing-page">
      {/* Stock Ticker - Top Banner */}
      <div className="ticker-banner">
        <StockTicker />
      </div>
      
      {/* Navigation */}
      <Navbar />
      
      {/* Hero Section */}
      <Hero />
      
      {/* Features Section */}
      <Features />
      
      {/* How It Works Section */}
      <HowItWorks />
      
      {/* Trending Memes Section */}
      <TrendingMemes />
      
      {/* Leaderboard Section */}
      <Leaderboard />
      
      {/* Footer */}
      <Footer />
    </div>
  );
};

export default LandingPage;
