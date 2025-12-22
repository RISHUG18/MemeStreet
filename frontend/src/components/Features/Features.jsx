import React from 'react';
import { 
  TrendingUp, 
  Shield, 
  Zap, 
  Trophy,
  Wallet,
  BarChart3
} from 'lucide-react';
import './Features.css';

const featuresData = [
  {
    icon: TrendingUp,
    title: 'Real-Time Pricing',
    description: 'Meme prices update based on upvotes, comments, and shares. Watch your investments grow with viral content.',
    color: 'green'
  },
  {
    icon: Wallet,
    title: 'Virtual Wallet',
    description: 'Start with 100 coins and build your empire. Buy low, sell high, and master the meme market.',
    color: 'cyan'
  },
  {
    icon: BarChart3,
    title: 'Portfolio Tracking',
    description: 'Track all your meme investments in one place. See gains, losses, and historical performance.',
    color: 'purple'
  },
  {
    icon: Trophy,
    title: 'Leaderboards',
    description: 'Compete with traders worldwide. Climb the ranks and earn Street Cred for your trading skills.',
    color: 'gold'
  },
  {
    icon: Zap,
    title: 'Meme IPOs',
    description: 'Be first to invest in newly listed memes. Catch the next viral sensation before it moons.',
    color: 'blue'
  },
  {
    icon: Shield,
    title: 'Fair Trading',
    description: 'IPO price caps prevent manipulation. Everyone gets a fair shot at the hottest memes.',
    color: 'red'
  }
];

const Features = () => {
  return (
    <section id="features" className="features-section">
      <div className="features-container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">Features</span>
          <h2 className="section-title">
            Everything You Need to
            <span className="gradient-text"> Dominate the Market</span>
          </h2>
          <p className="section-subtitle">
            Built for traders who understand that memes are the currency of the internet.
          </p>
        </div>

        {/* Features Grid */}
        <div className="features-grid">
          {featuresData.map((feature, index) => (
            <div key={index} className={`feature-card feature-${feature.color}`}>
              <div className={`feature-icon icon-${feature.color}`}>
                <feature.icon size={28} />
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
