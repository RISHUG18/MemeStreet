import React from 'react';
import { Rocket, Twitter, MessageCircle, Github } from 'lucide-react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      {/* CTA Section */}
      <div className="footer-cta">
        <div className="footer-cta-content">
          <h2 className="footer-cta-title">
            Ready to Trade <span className="gradient-text">Memes</span>?
          </h2>
          <p className="footer-cta-subtitle">
            Join thousands of traders in the meme economy. Start with 100 free coins today.
          </p>
          <button className="btn btn-footer-primary">
            Launch App
            <Rocket size={18} />
          </button>
        </div>
      </div>

      {/* Main Footer */}
      <div className="footer-main">
        <div className="footer-container">
          <div className="footer-grid">
            {/* Brand */}
            <div className="footer-brand">
              <div className="footer-logo">
                <Rocket className="footer-logo-icon" />
                <span className="footer-logo-text">
                  Meme<span className="gradient-text">Street</span>
                </span>
              </div>
              <p className="footer-description">
                The Wall Street of Internet Culture. Trade memes, build your portfolio, become a legend.
              </p>
              <div className="footer-socials">
                <a href="#" className="social-link">
                  <Twitter size={20} />
                </a>
                <a href="#" className="social-link">
                  <MessageCircle size={20} />
                </a>
                <a href="#" className="social-link">
                  <Github size={20} />
                </a>
              </div>
            </div>

            {/* Links */}
            <div className="footer-links-group">
              <h4 className="footer-links-title">Product</h4>
              <ul className="footer-links">
                <li><a href="#">Trade</a></li>
                <li><a href="#">Portfolio</a></li>
                <li><a href="#">Leaderboard</a></li>
                <li><a href="#">IPO Calendar</a></li>
              </ul>
            </div>

            <div className="footer-links-group">
              <h4 className="footer-links-title">Resources</h4>
              <ul className="footer-links">
                <li><a href="#">How It Works</a></li>
                <li><a href="#">Pricing Guide</a></li>
                <li><a href="#">API Docs</a></li>
                <li><a href="#">Blog</a></li>
              </ul>
            </div>

            <div className="footer-links-group">
              <h4 className="footer-links-title">Company</h4>
              <ul className="footer-links">
                <li><a href="#">About Us</a></li>
                <li><a href="#">Careers</a></li>
                <li><a href="#">Contact</a></li>
                <li><a href="#">Press Kit</a></li>
              </ul>
            </div>
          </div>

          {/* Bottom */}
          <div className="footer-bottom">
            <p className="footer-copyright">
              © 2024 MemeStreet. All rights reserved. Built for the meme economy.
            </p>
            <div className="footer-legal">
              <a href="#">Privacy Policy</a>
              <a href="#">Terms of Service</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
