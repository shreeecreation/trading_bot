from datetime import datetime
from typing import Optional, Dict

class MarketBias:
    def __init__(
        self,
        symbol: str,
        bias: str,
        direction: str,
        strength: str,
        score: float,
        prev_price: float,
        current_price: float,
        change_percentage: float,
        daily_score: float,
        weekly_score: Optional[float] = None,
        daily_recommendation: Optional[str] = None,
        weekly_recommendation: Optional[str] = None,
        indicators: Optional[Dict] = None,
        timestamp: Optional[datetime] = None
    ):
        self.id = None  # You can manage this manually if needed
        self.symbol = symbol
        self.timestamp = timestamp or datetime.utcnow()
        self.bias = bias
        self.direction = direction
        self.strength = strength
        self.score = score
        self.prev_price = prev_price
        self.current_price = current_price
        self.change_percentage = change_percentage
        self.daily_score = daily_score
        self.weekly_score = weekly_score
        self.daily_recommendation = daily_recommendation
        self.weekly_recommendation = weekly_recommendation
        self.indicators = indicators or {}

    def __repr__(self):
        return f"<MarketBias {self.symbol} {self.timestamp.isoformat()} {self.bias}>"

    def to_dict(self):
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
