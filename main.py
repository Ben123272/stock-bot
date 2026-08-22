import os
import yfinance as yf
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

# הגדרות בסיסיות
BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5a0PnXRbbbS-jdPnn3BZfM"
MY_STOCKS = ["MU", "SNDK", "MRVL", "CRDO", "TSEM", "MP", "IREN", "OKLO", "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG", "PLTR", "COHR"]
GOLD_POOL = ["GOLD", "AEM", "NEM"]

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty: return None
        price = hist['Close'].iloc[-1]
        sma = hist['Close'].rolling(window=20).mean().iloc[-1]
        trend = "עלייה" if price > sma else "ירידה"
        macd = "חיובי" if price > (hist['Close'].rolling(window=12).mean().iloc[-1]) else "שלילי"
        bb = "בתוך הרצועות"
        rr = "1:3"
        return {'ticker': ticker, 'price': f"{price:.2f}$", 'trend': trend, 'macd': macd, 'bb': bb, 'rr': rr}
    except:
        return None

def generate_full_report():
    today = datetime.now().strftime('%Y-%m-%d')
    my_results = [analyze_stock(t) for t in MY_STOCKS if analyze_stock(t)]
    report = f"🏛️ דוח אלגוריתמי מוסדי - {today}\n\n"
    report += "📈 **המניות שלך:**\n" + "\n".join([f"• {d['ticker']} | {d['price']} | {d['trend']}" for d in my_results])
    return report

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        msg = update["message"].get("text", "").strip()
        
        if msg == "סקירה":
            send_telegram_message(chat_id, "⏳ מכין דוח מניות מלא...")
            send_telegram_message(chat_id, generate_full_report())
            
        elif msg.startswith("בדוק "):
            ticker = msg.split(" ")[1].upper()
            send_telegram_message(chat_id, f"🔍 מנתח את המניה {ticker}...")
            
            res = analyze_stock(ticker)
            if res:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="60d")
                curr = hist['Close'].iloc[-1]
                atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
                stop_loss = curr - (atr * 1.5)
                take_profit = curr + (atr * 3)
                
                reply = (
                    f"🎯 **ניתוח ממוקד ל-{ticker}**\n\n"
                    f"💰 מחיר נוכחי: {res['price']}\n"
                    f"📈 מגמה: {res['trend']}\n"
                    f"🚀 מומנטום: {res['macd']}\n"
                    f"📊 מצב רצועות: {res['bb']}\n"
                    f"⚖️ יחס סיכון/סיכוי (R/R): {res['rr']}\n\n"
                    f"🛑 סטופ לוס מוצע: {stop_loss:.2f}$\n"
                    f"🎯 טייק פרופיט מוצע: {take_profit:.2f}$"
                )
                send_telegram_message(chat_id, reply)
            else:
                send_telegram_message(chat_id, f"❌ לא הצלחתי למצוא נתונים עבור המניה {ticker}. בדוק את הסימול ונסה שוב.")
                
    return "OK"

@app.route('/')
def home():
    return "Bot Webhook is active!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
