# Script to test different combinations for TradingView symbols
from tradingview_ta import TA_Handler, Interval
import logging

logging.basicConfig(level=logging.INFO)

def try_symbol(symbol, exchange, screener="forex"):
    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener=screener,
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        print(f"SUCCESS! Symbol: {symbol}, Exchange: {exchange}, Screener: {screener}")
        print(f"Close: {analysis.indicators['close']}")
        return True
    except Exception as e:
        print(f"FAILED: Symbol: {symbol}, Exchange: {exchange}, Screener: {screener}")
        print(f"Error: {str(e)}")
        return False

# Try various combinations for gold
symbols = ["XAUUSD", "XAU/USD", "GOLD", "XAU_USD", "GC"]
exchanges = ["FX", "FX_IDC", "OANDA", "FXCM", "FOREXCOM", "GLOBALPRIME", "CAPITALCOM"]
screeners = ["forex", "crypto", "cfd"]

found = False

# First test a known working stock symbol as baseline
print("\n===== Testing baseline (Apple stock) =====\n")
baseline = try_symbol("AAPL", "NASDAQ", "america")
if not baseline:
    print("\nWarning: Baseline test failed. TradingView API might be having issues.\n")

# Try combinations for gold
print("\n===== Testing Gold Symbol Combinations =====\n")
for screener in screeners:
    for exchange in exchanges:
        for symbol in symbols:
            if try_symbol(symbol, exchange, screener):
                found = True
                print(f"\nFound working combination: Symbol={symbol}, Exchange={exchange}, Screener={screener}\n")

if not found:
    print("\nNo working combination found for gold. Check if TradingView's API is available.\n")
