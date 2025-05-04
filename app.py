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
        
        # Fetch data from TradingView for daily and weekly analysis
        daily_handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY
        )
        
        weekly_handler = TA_Handler(
            symbol=symbol,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_WEEK
        )
        
        # Get the daily and weekly analysis
        try:
            daily_analysis = daily_handler.get_analysis()
            weekly_analysis = weekly_handler.get_analysis()
            
            # Check if data was fetched successfully
            if not hasattr(daily_analysis, 'indicators') or 'close' not in daily_analysis.indicators:
                return jsonify({
                    'status': 'error',
                    'message': 'Not enough daily data available for this symbol.'
                })
            
            if not hasattr(weekly_analysis, 'indicators') or 'close' not in weekly_analysis.indicators:
                logging.warning("Weekly data not available, proceeding with daily data only")
                has_weekly_data = False
            else:
                has_weekly_data = True
            
            # Get current price information from daily timeframe
            current_close = float(daily_analysis.indicators['close'])
            prev_open = float(daily_analysis.indicators['open'])
            
            logging.info(f"Daily timeframe - Previous open: {prev_open}, Current close: {current_close}")
            
            # Get weekly price information if available
            if has_weekly_data:
                weekly_close = float(weekly_analysis.indicators['close'])
                weekly_open = float(weekly_analysis.indicators['open'])
                # Get last 5 weeks' closes if available
                weekly_prev_close = weekly_analysis.indicators.get('prev_close', weekly_open)
                
                logging.info(f"Weekly timeframe - Weekly open: {weekly_open}, Weekly close: {weekly_close}")
        
        except Exception as e:
            logging.error(f"Error fetching analysis data: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error analyzing market data: {str(e)}'
            })
        
        # Determine market bias using institutional trading techniques and TradingView indicators
        daily_change_percentage = ((current_close - prev_open) / prev_open) * 100
        
        # Get additional indicators from TradingView daily analysis
        rsi = daily_analysis.indicators.get('RSI', 50)  # Relative Strength Index
        macd = daily_analysis.indicators.get('MACD.macd', 0)  # MACD Line
        signal = daily_analysis.indicators.get('MACD.signal', 0)  # MACD Signal Line
        ema_20 = daily_analysis.indicators.get('EMA20', current_close)  # 20-day EMA
        ema_50 = daily_analysis.indicators.get('EMA50', current_close)  # 50-day EMA
        stoch_k = daily_analysis.indicators.get('Stoch.K', 50)  # Stochastic %K
        stoch_d = daily_analysis.indicators.get('Stoch.D', 50)  # Stochastic %D
        
        # Get weekly indicators if available
        weekly_rsi = None
        weekly_macd = None
        weekly_signal = None
        weekly_ema_20 = None
        weekly_ema_50 = None
        weekly_change_percentage = None
        
        if has_weekly_data:
            weekly_change_percentage = ((weekly_close - weekly_open) / weekly_open) * 100
            weekly_rsi = weekly_analysis.indicators.get('RSI', 50)
            weekly_macd = weekly_analysis.indicators.get('MACD.macd', 0)
            weekly_signal = weekly_analysis.indicators.get('MACD.signal', 0)
            weekly_ema_20 = weekly_analysis.indicators.get('EMA20', weekly_close)
            weekly_ema_50 = weekly_analysis.indicators.get('EMA50', weekly_close)
            
            logging.info(f"Weekly RSI: {weekly_rsi}, Weekly Change: {weekly_change_percentage}%")
        
        # Get TradingView's recommendation
        daily_recommendation = daily_analysis.summary.get('RECOMMENDATION', '')
        weekly_recommendation = weekly_analysis.summary.get('RECOMMENDATION', '') if has_weekly_data else ''
        
        logging.info(f"Daily TradingView recommendation: {daily_recommendation}")
        if has_weekly_data:
            logging.info(f"Weekly TradingView recommendation: {weekly_recommendation}")
        
        # Calculate bias score (positive = bullish, negative = bearish)
        daily_bias_score = 0
        weekly_bias_score = 0
        
        # Daily timeframe analysis (70% weight in final score)
        # Price action component (40% weight)
        price_action = current_close - prev_open
        if price_action > 0:
            daily_bias_score += 40
        elif price_action < 0:
            daily_bias_score -= 40
            
        # Trend component (30% weight)
        if current_close > ema_20 and ema_20 > ema_50:
            daily_bias_score += 30  # Strong uptrend
        elif current_close < ema_20 and ema_20 < ema_50:
            daily_bias_score -= 30  # Strong downtrend
        elif current_close > ema_20:
            daily_bias_score += 15  # Moderate uptrend
        elif current_close < ema_20:
            daily_bias_score -= 15  # Moderate downtrend
            
        # Momentum component (20% weight)
        if rsi > 60:
            daily_bias_score += 20  # Strong bullish momentum
        elif rsi < 40:
            daily_bias_score -= 20  # Strong bearish momentum
        elif rsi > 50:
            daily_bias_score += 10  # Moderate bullish momentum
        elif rsi < 50:
            daily_bias_score -= 10  # Moderate bearish momentum
            
        # MACD component (10% weight)
        if macd > signal:
            daily_bias_score += 10  # Bullish MACD crossover
        elif macd < signal:
            daily_bias_score -= 10  # Bearish MACD crossover
            
        logging.info(f"Daily bias score: {daily_bias_score}")
        
        # Weekly timeframe analysis (30% weight in final score) if available
        if has_weekly_data:
            # Weekly price action (40% weight)
            if weekly_close > weekly_open:
                weekly_bias_score += 40
            elif weekly_close < weekly_open:
                weekly_bias_score -= 40
                
            # Weekly trend component (30% weight)
            if weekly_close > weekly_ema_20 and weekly_ema_20 > weekly_ema_50:
                weekly_bias_score += 30  # Strong uptrend
            elif weekly_close < weekly_ema_20 and weekly_ema_20 < weekly_ema_50:
                weekly_bias_score -= 30  # Strong downtrend
            elif weekly_close > weekly_ema_20:
                weekly_bias_score += 15  # Moderate uptrend
            elif weekly_close < weekly_ema_20:
                weekly_bias_score -= 15  # Moderate downtrend
                
            # Weekly momentum component (20% weight)
            if weekly_rsi > 60:
                weekly_bias_score += 20  # Strong bullish momentum
            elif weekly_rsi < 40:
                weekly_bias_score -= 20  # Strong bearish momentum
            elif weekly_rsi > 50:
                weekly_bias_score += 10  # Moderate bullish momentum
            elif weekly_rsi < 50:
                weekly_bias_score -= 10  # Moderate bearish momentum
                
            # Weekly MACD component (10% weight)
            if weekly_macd > weekly_signal:
                weekly_bias_score += 10  # Bullish MACD crossover
            elif weekly_macd < weekly_signal:
                weekly_bias_score -= 10  # Bearish MACD crossover
                
            logging.info(f"Weekly bias score: {weekly_bias_score}")
        
        # Calculate final bias score: 70% daily + 30% weekly (if available)
        bias_score = daily_bias_score * 0.7
        if has_weekly_data:
            bias_score += weekly_bias_score * 0.3
            
        logging.info(f"Final bias score (with weekly data): {bias_score}")
        
        # This conflict check was moved to the response formatting section
        
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
        
        # Handle the strength modifier for conflicting timeframes
        strength_modifier = None
        if has_weekly_data and ((daily_bias_score > 30 and weekly_bias_score < -30) or 
                               (daily_bias_score < -30 and weekly_bias_score > 30)):
            strength_modifier = "conflicted"  # Daily and weekly timeframes disagreeing
            strength = "conflicted"
            logging.info("Conflicting signals between daily and weekly timeframes")
            
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
            'change_percentage': round(daily_change_percentage, 2),
            'timeframes': {
                'daily': {
                    'score': daily_bias_score,
                    'change_percentage': round(daily_change_percentage, 2),
                    'recommendation': daily_recommendation
                }
            },
            'indicators': {  # Added technical indicators for advanced users
                'rsi': round(rsi, 2) if isinstance(rsi, (int, float)) else rsi,
                'ema20': round(ema_20, 4) if isinstance(ema_20, (int, float)) else ema_20,
                'ema50': round(ema_50, 4) if isinstance(ema_50, (int, float)) else ema_50,
                'macd': round(macd, 4) if isinstance(macd, (int, float)) else macd,
                'macd_signal': round(signal, 4) if isinstance(signal, (int, float)) else signal,
                'stoch_k': round(stoch_k, 2) if isinstance(stoch_k, (int, float)) else stoch_k,
                'stoch_d': round(stoch_d, 2) if isinstance(stoch_d, (int, float)) else stoch_d
            }
        }
        
        # Add weekly data if available
        if has_weekly_data:
            # Safe rounding for values that might be None
            safe_round = lambda x, digits: round(float(x), digits) if x is not None and isinstance(x, (int, float)) else None
            
            response['timeframes']['weekly'] = {
                'score': weekly_bias_score,
                'change_percentage': safe_round(weekly_change_percentage, 2),
                'recommendation': weekly_recommendation,
                'indicators': {
                    'rsi': safe_round(weekly_rsi, 2),
                    'macd': safe_round(weekly_macd, 4),
                    'macd_signal': safe_round(weekly_signal, 4)
                }
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
