import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import './StockTicker.css';

const tickerData = [
  { name: 'DOGE', price: 420.69, change: 12.5, up: true },
  { name: 'PEPE', price: 156.32, change: -3.2, up: false },
  { name: 'WOJAK', price: 89.99, change: 8.7, up: true },
  { name: 'CHAD', price: 234.50, change: 15.3, up: true },
  { name: 'STONKS', price: 999.99, change: -5.1, up: false },
  { name: 'MOON', price: 567.89, change: 22.1, up: true },
  { name: 'HODL', price: 345.67, change: 4.5, up: true },
  { name: 'FOMO', price: 123.45, change: -8.9, up: false },
  { name: 'YOLO', price: 789.01, change: 18.2, up: true },
  { name: 'GG', price: 45.67, change: -2.3, up: false },
];

const StockTicker = () => {
  // Double the data for seamless loop
  const doubledData = [...tickerData, ...tickerData];

  return (
    <div className="ticker-wrapper">
      <div className="ticker-track">
        {doubledData.map((stock, index) => (
          <div key={index} className="ticker-item">
            <span className="ticker-symbol">${stock.name}</span>
            <span className="ticker-price">{stock.price.toFixed(2)}</span>
            <span className={`ticker-change ${stock.up ? 'up' : 'down'}`}>
              {stock.up ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {stock.up ? '+' : ''}{stock.change}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StockTicker;
