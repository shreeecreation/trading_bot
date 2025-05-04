import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your Telegram bot token

# Fetch today's market bias for EURUSD using 1D data
def get_daily_bias():
    data = yf.download("EURUSD=X", period="5d", interval="1d")
    if data.empty or len(data) < 2:
        return "Not enough data to determine bias."

    prev_close = data['Close'].iloc[-2]
    current_close = data['Close'].iloc[-1]

    if current_close > prev_close:
        return f"📈 Daily Bias: **Bullish**\n{prev_close:.4f} → {current_close:.4f}"
    elif current_close < prev_close:
        return f"📉 Daily Bias: **Bearish**\n{prev_close:.4f} → {current_close:.4f}"
    else:
        return "🔁 Daily Bias: **Sideways** (No major change)"

# Telegram command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bias = get_daily_bias()
    await update.message.reply_text(bias)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot running...")
    app.run_polling()
