import os
import logging
import yfinance as yf
from flask import Flask, render_template, request, jsonify
import pandas as pd

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
        
        # Make sure the currency pair has the correct format for yfinance
        if not currency_pair.endswith('=X') and not currency_pair.startswith('^'):
            if currency_pair.upper() in ['XAUUSD', 'GOLD']:
                currency_pair = 'GC=F'  # Gold Futures
            elif currency_pair.upper() in ['XAGUSD', 'SILVER']:
                currency_pair = 'SI=F'  # Silver Futures
            elif len(currency_pair) == 6:
                # For regular currency pairs like EURUSD, GBPUSD
                currency_pair = f"{currency_pair}=X"
            elif currency_pair.upper() in ['SPX', 'S&P500', 'SP500']:
                currency_pair = '^GSPC'  # S&P 500 index
            elif currency_pair.upper() in ['DJI', 'DOW', 'DOWJONES']:
                currency_pair = '^DJI'  # Dow Jones Industrial Average
        
        # Fetch data
        data = yf.download(currency_pair, period="5d", interval="1d")
        
        # Check if data was fetched successfully
        if data.empty or len(data) < 2:
            return jsonify({
                'status': 'error',
                'message': 'Not enough data available for this symbol.'
            })
        
        # Get previous and current close prices
        prev_close = data['Close'].iloc[-2]
        current_close = data['Close'].iloc[-1]
        
        # Determine market bias
        change_percentage = ((current_close - prev_close) / prev_close) * 100
        
        if current_close > prev_close:
            bias = "Bullish"
            direction = "up"
            icon = "📈"
        elif current_close < prev_close:
            bias = "Bearish"
            direction = "down"
            icon = "📉"
        else:
            bias = "Sideways"
            direction = "neutral"
            icon = "🔁"
        
        # Format the response data
        response = {
            'status': 'success',
            'symbol': currency_pair.replace('=X', ''),
            'bias': bias,
            'direction': direction,
            'icon': icon,
            'prev_close': round(prev_close, 4),
            'current_close': round(current_close, 4),
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
