# Test TradingView data access
from tradingview_ta import TA_Handler, Interval
import logging

logging.basicConfig(level=logging.INFO)

try:
    # Initialize the TA_Handler for XAUUSD (Gold)
    handler = TA_Handler(
        symbol="XAUUSD",
        screener="cfd",
        exchange="FOREXCOM",
        interval=Interval.INTERVAL_1_DAY
    )
    
    # Get the analysis
    analysis = handler.get_analysis()
    
    # Display the data
    print("\n=== TradingView Data Test ===\n")
    print(f"Symbol: {handler.symbol}")
    print(f"Exchange: {handler.exchange}")
    print(f"Interval: {handler.interval}")
    
    print("\n=== Price Information ===\n")
    if hasattr(analysis, 'indicators'):
        print(f"Close: {analysis.indicators['close']}")
        print(f"Open: {analysis.indicators['open']}")
        print(f"High: {analysis.indicators['high']}")
        print(f"Low: {analysis.indicators['low']}")
        
        # Calculate change
        current = analysis.indicators['close']
        previous = analysis.indicators['open']
        change = ((current - previous) / previous) * 100
        print(f"\nChange %: {change:.2f}%")
        
        # Determine market bias
        if current > previous:
            print("Market Bias: Bullish 📈")
        elif current < previous:
            print("Market Bias: Bearish 📉")
        else:
            print("Market Bias: Sideways 🔁")
    else:
        print("No indicator data available")
    
    # Show the recommendation
    print(f"\nTradingView Summary: {analysis.summary['RECOMMENDATION']}")
    
except Exception as e:
    print(f"Error: {str(e)}")
