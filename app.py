import os
import logging
from flask import Flask, render_template, request, jsonify
from tradingview_ta import TA_Handler, Interval

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key")

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/get_market_bias', methods=['POST'])
def get_market_bias():
    """Fetch and return market bias for a specified currency pair."""
    try:
        # Get currency pair from form
        currency_pair = request.form.get('currency_pair', 'EURUSD=X')
        logging.info(f"Requested currency pair: {currency_pair}")
        
        # Set up TradingView parameters based on currency pair
        # Default to forex
        symbol = currency_pair
        screener = "forex"
        exchange = "FX_IDC"
        
        # Special cases for specific symbols
        if currency_pair.upper() in ['XAUUSD', 'GOLD']:
            symbol = "XAUUSD"
            screener = "cfd"
            exchange = "FOREXCOM"
        elif currency_pair.upper() in ['BTCUSD', 'BTC', 'BITCOIN']:
            symbol = "BTCUSD"
            screener = "crypto"
            exchange = "BINANCE"
        
        logging.info(f"TradingView parameters: Symbol={symbol}, Exchange={exchange}, Screener={screener}")
        
        # Fetch data from TradingView
        handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY
        )
        
        # Get the analysis
        analysis = handler.get_analysis()
        
        # Check if data was fetched successfully
        if not hasattr(analysis, 'indicators') or 'close' not in analysis.indicators:
            return jsonify({
                'status': 'error',
                'message': 'Not enough data available for this symbol.'
            })
        
        # Get current price information
        current_close = float(analysis.indicators['close'])
        prev_open = float(analysis.indicators['open'])
        
        logging.info(f"Previous open: {prev_open}, Current close: {current_close}")
        
        # Determine market bias using institutional trading techniques and TradingView indicators
        change_percentage = ((current_close - prev_open) / prev_open) * 100
        
        # Get additional indicators from TradingView analysis
        rsi = analysis.indicators.get('RSI', 50)  # Relative Strength Index
        macd = analysis.indicators.get('MACD.macd', 0)  # MACD Line
        signal = analysis.indicators.get('MACD.signal', 0)  # MACD Signal Line
        ema_20 = analysis.indicators.get('EMA20', current_close)  # 20-day EMA
        ema_50 = analysis.indicators.get('EMA50', current_close)  # 50-day EMA
        stoch_k = analysis.indicators.get('Stoch.K', 50)  # Stochastic %K
        stoch_d = analysis.indicators.get('Stoch.D', 50)  # Stochastic %D
        
        # Get TradingView's recommendation
        tv_recommendation = analysis.summary.get('RECOMMENDATION', '')
        logging.info(f"TradingView recommendation: {tv_recommendation}")
        
        # Calculate bias score (positive = bullish, negative = bearish)
        bias_score = 0
        
        # Price action component (40% weight)
        price_action = current_close - prev_open
        if price_action > 0:
            bias_score += 40
        elif price_action < 0:
            bias_score -= 40
            
        # Trend component (30% weight)
        if current_close > ema_20 and ema_20 > ema_50:
            bias_score += 30  # Strong uptrend
        elif current_close < ema_20 and ema_20 < ema_50:
            bias_score -= 30  # Strong downtrend
        elif current_close > ema_20:
            bias_score += 15  # Moderate uptrend
        elif current_close < ema_20:
            bias_score -= 15  # Moderate downtrend
            
        # Momentum component (20% weight)
        if rsi > 60:
            bias_score += 20  # Strong bullish momentum
        elif rsi < 40:
            bias_score -= 20  # Strong bearish momentum
        elif rsi > 50:
            bias_score += 10  # Moderate bullish momentum
        elif rsi < 50:
            bias_score -= 10  # Moderate bearish momentum
            
        # MACD component (10% weight)
        if macd > signal:
            bias_score += 10  # Bullish MACD crossover
        elif macd < signal:
            bias_score -= 10  # Bearish MACD crossover
        
        # Determine final bias based on score
        if bias_score >= 50:
            bias = "Strong Bullish"
            direction = "up"
            icon = "📈"
            strength = "strong"
            logging.info(f"Determined bias: Strong Bullish (score: {bias_score})")
        elif bias_score >= 20:
            bias = "Bullish"
            direction = "up"
            icon = "📈"
            strength = "moderate"
            logging.info(f"Determined bias: Bullish (score: {bias_score})")
        elif bias_score <= -50:
            bias = "Strong Bearish"
            direction = "down"
            icon = "📉"
            strength = "strong"
            logging.info(f"Determined bias: Strong Bearish (score: {bias_score})")
        elif bias_score <= -20:
            bias = "Bearish"
            direction = "down"
            icon = "📉"
            strength = "moderate"
            logging.info(f"Determined bias: Bearish (score: {bias_score})")
        else:
            bias = "Sideways"
            direction = "neutral"
            icon = "🔁"
            strength = "weak"
            logging.info(f"Determined bias: Sideways (score: {bias_score})")
        
        # Format the response data
        response = {
            'status': 'success',
            'symbol': currency_pair,
            'bias': bias,
            'direction': direction,
            'icon': icon,
            'strength': strength,  # Added bias strength for frontend display
            'score': bias_score,   # Added numerical score for transparency
            'prev_price': round(prev_open, 4),  # Using open price from TradingView
            'current_price': round(current_close, 4),
            'change_percentage': round(change_percentage, 2),
            'indicators': {  # Added technical indicators for advanced users
                'rsi': round(rsi, 2) if isinstance(rsi, (int, float)) else rsi,
                'ema20': round(ema_20, 4) if isinstance(ema_20, (int, float)) else ema_20,
                'ema50': round(ema_50, 4) if isinstance(ema_50, (int, float)) else ema_50,
                'macd': round(macd, 4) if isinstance(macd, (int, float)) else macd,
                'macd_signal': round(signal, 4) if isinstance(signal, (int, float)) else signal,
                'stoch_k': round(stoch_k, 2) if isinstance(stoch_k, (int, float)) else stoch_k,
                'stoch_d': round(stoch_d, 2) if isinstance(stoch_d, (int, float)) else stoch_d
            },
            'tv_recommendation': tv_recommendation  # TradingView's own recommendation
        }
        
        return jsonify(response)
    
    except Exception as e:
        logging.error(f"Error fetching market data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching market data: {str(e)}'
        })

@app.route('/get_supported_pairs')
def get_supported_pairs():
    """Return a list of supported currency pairs."""
    pairs = [
        {'symbol': 'EURUSD', 'name': 'Euro / US Dollar'},
        {'symbol': 'GBPUSD', 'name': 'British Pound / US Dollar'},
        {'symbol': 'USDJPY', 'name': 'US Dollar / Japanese Yen'},
        {'symbol': 'AUDUSD', 'name': 'Australian Dollar / US Dollar'},
        {'symbol': 'USDCAD', 'name': 'US Dollar / Canadian Dollar'},
        {'symbol': 'USDCHF', 'name': 'US Dollar / Swiss Franc'},
        {'symbol': 'NZDUSD', 'name': 'New Zealand Dollar / US Dollar'},
        {'symbol': 'XAUUSD', 'name': 'Gold / US Dollar'},
        {'symbol': 'BTCUSD', 'name': 'Bitcoin / US Dollar'}
    ]
    return jsonify(pairs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
