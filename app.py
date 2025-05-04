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
    return render_template('index.html')

@app.route('/get_market_bias', methods=['POST'])
def get_market_bias():
    try:
        currency_pair = request.form.get('currency_pair', 'EURUSD=X')
        logging.info(f"Requested currency pair: {currency_pair}")
        
        symbol = currency_pair
        screener = "forex"
        exchange = "FX_IDC"

        if currency_pair.upper() in ['XAUUSD', 'GOLD']:
            symbol = "XAUUSD"
            screener = "cfd"
            exchange = "FOREXCOM"
        elif currency_pair.upper() in ['BTCUSD', 'BTC', 'BITCOIN']:
            symbol = "BTCUSD"
            screener = "crypto"
            exchange = "BINANCE"

        logging.info(f"TradingView parameters: Symbol={symbol}, Exchange={exchange}, Screener={screener}")

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

        try:
            daily_analysis = daily_handler.get_analysis()
            weekly_analysis = weekly_handler.get_analysis()

            if not hasattr(daily_analysis, 'indicators') or 'close' not in daily_analysis.indicators:
                return jsonify({'status': 'error', 'message': 'Not enough daily data available for this symbol.'})

            has_weekly_data = hasattr(weekly_analysis, 'indicators') and 'close' in weekly_analysis.indicators

            current_close = float(daily_analysis.indicators['close'])
            prev_open = float(daily_analysis.indicators['open'])

            if has_weekly_data:
                weekly_close = float(weekly_analysis.indicators['close'])
                weekly_open = float(weekly_analysis.indicators['open'])

        except Exception as e:
            logging.error(f"Error fetching analysis data: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Error analyzing market data: {str(e)}'})

        daily_change_percentage = ((current_close - prev_open) / prev_open) * 100

        rsi = daily_analysis.indicators.get('RSI', 50)
        macd = daily_analysis.indicators.get('MACD.macd', 0)
        signal = daily_analysis.indicators.get('MACD.signal', 0)
        ema_20 = daily_analysis.indicators.get('EMA20', current_close)
        ema_50 = daily_analysis.indicators.get('EMA50', current_close)
        stoch_k = daily_analysis.indicators.get('Stoch.K', 50)
        stoch_d = daily_analysis.indicators.get('Stoch.D', 50)

        weekly_rsi = weekly_macd = weekly_signal = weekly_ema_20 = weekly_ema_50 = weekly_change_percentage = None

        if has_weekly_data:
            weekly_change_percentage = ((weekly_close - weekly_open) / weekly_open) * 100
            weekly_rsi = weekly_analysis.indicators.get('RSI', 50)
            weekly_macd = weekly_analysis.indicators.get('MACD.macd', 0)
            weekly_signal = weekly_analysis.indicators.get('MACD.signal', 0)
            weekly_ema_20 = weekly_analysis.indicators.get('EMA20', weekly_close)
            weekly_ema_50 = weekly_analysis.indicators.get('EMA50', weekly_close)

        daily_recommendation = daily_analysis.summary.get('RECOMMENDATION', '')
        weekly_recommendation = weekly_analysis.summary.get('RECOMMENDATION', '') if has_weekly_data else ''

        daily_bias_score = weekly_bias_score = 0

        if current_close > prev_open:
            daily_bias_score += 40
        elif current_close < prev_open:
            daily_bias_score -= 40

        if current_close > ema_20 and ema_20 > ema_50:
            daily_bias_score += 30
        elif current_close < ema_20 and ema_20 < ema_50:
            daily_bias_score -= 30
        elif current_close > ema_20:
            daily_bias_score += 15
        elif current_close < ema_20:
            daily_bias_score -= 15

        if rsi > 60:
            daily_bias_score += 20
        elif rsi < 40:
            daily_bias_score -= 20
        elif rsi > 50:
            daily_bias_score += 10
        elif rsi < 50:
            daily_bias_score -= 10

        if macd > signal:
            daily_bias_score += 10
        elif macd < signal:
            daily_bias_score -= 10

        if has_weekly_data:
            if weekly_close > weekly_open:
                weekly_bias_score += 40
            elif weekly_close < weekly_open:
                weekly_bias_score -= 40

            if weekly_close > weekly_ema_20 and weekly_ema_20 > weekly_ema_50:
                weekly_bias_score += 30
            elif weekly_close < weekly_ema_20 and weekly_ema_20 < weekly_ema_50:
                weekly_bias_score -= 30
            elif weekly_close > weekly_ema_20:
                weekly_bias_score += 15
            elif weekly_close < weekly_ema_20:
                weekly_bias_score -= 15

            if weekly_rsi > 60:
                weekly_bias_score += 20
            elif weekly_rsi < 40:
                weekly_bias_score -= 20
            elif weekly_rsi > 50:
                weekly_bias_score += 10
            elif weekly_rsi < 50:
                weekly_bias_score -= 10

            if weekly_macd > weekly_signal:
                weekly_bias_score += 10
            elif weekly_macd < weekly_signal:
                weekly_bias_score -= 10

        bias_score = daily_bias_score * 0.7
        if has_weekly_data:
            bias_score += weekly_bias_score * 0.3

        if bias_score >= 50:
            bias = "Strong Bullish"
            direction = "up"
            icon = "📈"
            strength = "strong"
        elif bias_score >= 20:
            bias = "Bullish"
            direction = "up"
            icon = "📈"
            strength = "moderate"
        elif bias_score <= -50:
            bias = "Strong Bearish"
            direction = "down"
            icon = "📉"
            strength = "strong"
        elif bias_score <= -20:
            bias = "Bearish"
            direction = "down"
            icon = "📉"
            strength = "moderate"
        else:
            bias = "Sideways"
            direction = "neutral"
            icon = "🔁"
            strength = "weak"

        if has_weekly_data and ((daily_bias_score > 30 and weekly_bias_score < -30) or 
                                (daily_bias_score < -30 and weekly_bias_score > 30)):
            strength = "conflicted"

        response = {
            'status': 'success',
            'symbol': currency_pair,
            'bias': bias,
            'direction': direction,
            'icon': icon,
            'strength': strength,
            'score': bias_score,
            'prev_price': round(prev_open, 4),
            'current_price': round(current_close, 4),
            'change_percentage': round(daily_change_percentage, 2),
            'timeframes': {
                'daily': {
                    'score': daily_bias_score,
                    'change_percentage': round(daily_change_percentage, 2),
                    'recommendation': daily_recommendation
                }
            },
            'indicators': {
                'rsi': round(rsi, 2) if isinstance(rsi, (int, float)) else rsi,
                'ema20': round(ema_20, 4) if isinstance(ema_20, (int, float)) else ema_20,
                'ema50': round(ema_50, 4) if isinstance(ema_50, (int, float)) else ema_50,
                'macd': round(macd, 4) if isinstance(macd, (int, float)) else macd,
                'macd_signal': round(signal, 4) if isinstance(signal, (int, float)) else signal,
                'stoch_k': round(stoch_k, 2) if isinstance(stoch_k, (int, float)) else stoch_k,
                'stoch_d': round(stoch_d, 2) if isinstance(stoch_d, (int, float)) else stoch_d
            }
        }

        if has_weekly_data:
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
        return jsonify({'status': 'error', 'message': f'Error fetching market data: {str(e)}'})

@app.route('/get_supported_pairs')
def get_supported_pairs():
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
