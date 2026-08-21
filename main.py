import os
import time
import schedule
import yfinance as yf
import pandas as pd
import telebot

# הגדרות פרטי ההתקשרות
BOT_TOKEN = "8710966476:AAEEMZiiTBNWxrBYFmo3mK_eOGDAUZWaZis"
CHAT_ID = "8253548607"

bot = telebot.TeleBot(BOT_TOKEN)

# רשימת המניות למעקב
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
    
    # 1. סריקת רשימת המעקב
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
            
    # 2. שתי מניות הזדמנות (דוגמה)
    report += "\n🎯 *2 מניות הזדמנות מומלצות:*\n"
    opportunities = ["AAPL", "MSFT"]
    for ticker in opportunities:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            if df.empty:
                continue
            price = df['Close'].iloc[-1]
            rsi = calculate_rsi(df).iloc[-1]
            report += f"• *{ticker}*: ${price:.2f} | RSI: {rsi:.1f}\n"
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            
    # שליחת הדו"ח לטלגרם
    bot.send_message(CHAT_ID, report, parse_mode="Markdown")
    print("הדו\"ח נשלח בהצלחה!")

# שליחת הודעת אישור מיידית ברגע שהשרת עולה
try:
    bot.send_message(CHAT_ID, "🤖 *הבוט הופעל בהצלחה ב-Render!* הסריקה היומית מתוזמנת לשעה 20:00.", parse_mode="Markdown")
except Exception as e:
    print(f"Error sending start message: {e}")

# תזמון הריצה ל-17:00 UTC (20:00 שעון ישראל)
schedule.every().day.at("17:00").do(run_daily_scan)

while True:
    schedule.run_pending()
    time.sleep(60)
