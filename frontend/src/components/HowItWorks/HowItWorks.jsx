import React from 'react';
import { Search, ShoppingCart, TrendingUp, DollarSign } from 'lucide-react';
import './HowItWorks.css';

const steps = [
  {
    number: '01',
    icon: Search,
    title: 'Browse Memes',
    description: 'Explore trending memes on the market. Filter by price, popularity, or newest listings.'
  },
  {
    number: '02',
    icon: ShoppingCart,
    title: 'Buy Shares',
    description: 'Invest in memes you believe will go viral. The earlier you buy, the bigger your potential gains.'
  },
  {
    number: '03',
    icon: TrendingUp,
    title: 'Watch It Grow',
    description: 'As memes get upvoted and shared, their price increases. Your investment grows with their popularity.'
  },
  {
    number: '04',
    icon: DollarSign,
    title: 'Sell for Profit',
    description: 'Cash out when the price is right. Time the market and maximize your returns.'
  }
];

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="how-it-works-section">
      <div className="hiw-container">
        {/* Section Header */}
        <div className="section-header">
          <span className="section-tag">How It Works</span>
          <h2 className="section-title">
            Start Trading in
            <span className="gradient-text"> 4 Simple Steps</span>
          </h2>
          <p className="section-subtitle">
            No experience needed. Jump in and start building your meme portfolio today.
          </p>
        </div>

        {/* Steps */}
        <div className="steps-container">
          {steps.map((step, index) => (
            <div key={index} className="step-card">
              <div className="step-number">{step.number}</div>
              <div className="step-icon">
                <step.icon size={32} />
              </div>
              <h3 className="step-title">{step.title}</h3>
              <p className="step-description">{step.description}</p>
              
              {index < steps.length - 1 && (
                <div className="step-connector">
                  <div className="connector-line"></div>
                  <div className="connector-arrow">→</div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="hiw-cta">
          <button className="btn btn-hiw-primary">
            Get Started Now — It's Free
          </button>
          <p className="hiw-cta-note">No credit card required. Start with 100 free coins!</p>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
