from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON

db = SQLAlchemy()

class MarketBias(db.Model):
    __tablename__ = 'market_bias'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Bias data
    bias = Column(String(50), nullable=False)  # e.g., 'Bullish', 'Bearish', 'Sideways'
    direction = Column(String(20), nullable=False)  # 'up', 'down', 'neutral'
    strength = Column(String(20), nullable=False)  # 'strong', 'moderate', 'weak', 'conflicted'
    score = Column(Float, nullable=False)  # Bias score
    
    # Price data
    prev_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    change_percentage = Column(Float, nullable=False)
    
    # Timeframe data
    daily_score = Column(Float, nullable=False)
    weekly_score = Column(Float, nullable=True)  # Nullable as weekly data may not always be available
    daily_recommendation = Column(String(50), nullable=True)
    weekly_recommendation = Column(String(50), nullable=True)
    
    # Technical indicators
    indicators = Column(JSON, nullable=True)  # Store all indicators as JSON
    
    def __repr__(self):
        return f"<MarketBias {self.symbol} {self.timestamp} {self.bias}>"
    
    def to_dict(self):
        """Convert object to dictionary"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'bias': self.bias,
            'direction': self.direction,
            'strength': self.strength,
            'score': self.score,
            'prev_price': self.prev_price,
            'current_price': self.current_price,
            'change_percentage': self.change_percentage,
            'daily_score': self.daily_score,
            'weekly_score': self.weekly_score,
            'daily_recommendation': self.daily_recommendation,
            'weekly_recommendation': self.weekly_recommendation,
            'indicators': self.indicators
        }
