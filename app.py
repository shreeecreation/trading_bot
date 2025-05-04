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
        elif currency_pair.upper() in ['XAGUSD', 'SILVER']:
            symbol = "XAGUSD"
            screener = "cfd"
            exchange = "FOREXCOM"
        elif currency_pair.upper() in ['SPX', 'S&P500', 'SP500']:
            symbol = "SPX500"
            screener = "cfd"
            exchange = "FOREXCOM"
        elif currency_pair.upper() in ['DJI', 'DOW', 'DOWJONES']:
            symbol = "US30"
            screener = "cfd"
            exchange = "FOREXCOM"
        
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
        
        # Determine market bias using TradingView data
        # We compare current close with today's open
        change_percentage = ((current_close - prev_open) / prev_open) * 100
        
        # Use explicit numerical comparison to avoid any issues
        if (current_close - prev_open) > 0.0001:  # Small threshold for floating point comparison
            bias = "Bullish"
            direction = "up"
            icon = "📈"
            logging.info("Determined bias: Bullish")
        elif (prev_open - current_close) > 0.0001:  # Small threshold for floating point comparison
            bias = "Bearish"
            direction = "down"
            icon = "📉"
            logging.info("Determined bias: Bearish")
        else:
            bias = "Sideways"
            direction = "neutral"
            icon = "🔁"
            logging.info("Determined bias: Sideways")
        
        # Format the response data
        response = {
            'status': 'success',
            'symbol': currency_pair,
            'bias': bias,
            'direction': direction,
            'icon': icon,
            'prev_price': round(prev_open, 4),  # Using open price from TradingView
            'current_price': round(current_close, 4),
            'change_percentage': round(change_percentage, 2)
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
        {'symbol': 'XAGUSD', 'name': 'Silver / US Dollar'},
        {'symbol': 'SPX', 'name': 'S&P 500 Index'},
        {'symbol': 'DJI', 'name': 'Dow Jones Industrial Average'}
    ]
    return jsonify(pairs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
