import time
import schedule
import yfinance as yf
import pandas as pd
import telebot

BOT_TOKEN = "8710966476:AAEEMZiiTBNWxrBYFmo3mK_eOGDAUZWaZis"
CHAT_ID = "8253548607"

bot = telebot.TeleBot(BOT_TOKEN)

# 1. שליחת הודעת בדיקה מיד עם הפעלת הסקריפט
print("מנסה לשלוח הודעת בדיקה...")
try:
    bot.send_message(CHAT_ID, "🚀 הבוט מחובר בהצלחה ל-Render ועובד!")
    print("הודעת בדיקה נשלחה בהצלחה!")
except Exception as e:
    print(f"שגיאה בשליחה: {e}")

WATCHLIST = [
    "MU", "SNDK", "MRVL", "CRDO", "TSEM", "COHR", 
    "MP", "IREN", "OKLO", "VECO", "IBM", "GOOGL", 
    "AMD", "META", "NVDA", "CEG"
]

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_daily_scan():
    report = "📊 *דו\"ח סריקת מניות יומי*\n\n"
    report += "*מניות במעקב:*\n"
    for ticker in WATCHLIST:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            if df.empty or len(df) < 14:
                continue
            price = df['Close'].iloc[-1]
            rsi = calculate_rsi(df).iloc[-1]
            report += f"• *{ticker}*: ${price:.2f} | RSI: {rsi:.1f}\n"
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            
    bot.send_message(CHAT_ID, report, parse_mode="Markdown")

# תזמון יום-יומי ל-20:00 שעון ישראל (17:00 UTC)
schedule.every().day.at("17:00").do(run_daily_scan)

while True:
    schedule.run_pending()
    time.sleep(60)
