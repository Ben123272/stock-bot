import os
import time
import threading
import schedule
import yfinance as yf
import pandas as pd
import telebot
from flask import Flask

# הטוקן החדש והתקין
BOT_TOKEN = "8710966476:AAG0UXucvKBz0ISHrGiRzVhsG3_lsnLFFhM"
CHAT_ID = "8253548607"

bot = telebot.TeleBot(BOT_TOKEN)

# 1. שליחת הודעת בדיקה מיידית
print("מנסה לשלוח הודעת בדיקה...")
try:
    bot.send_message(CHAT_ID, "🚀 הבוט מחובר בהצלחה ל-Render ועובד!")
    print("הודעת בדיקה נשלחה בהצלחה!")
except Exception as e:
    print(f"שגיאה בשליחה: {e}")

# 2. הגדרת שרת ה-Web בשביל Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 3. הגדרת רשימת המעקב והסריקה
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

schedule.every().day.at("17:00").do(run_daily_scan)

# הרצת תזמון הסריקות ברקע
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# 4. הפעלת שרת ה-Web
if __name__ == "__main__":
    run_web_server()
