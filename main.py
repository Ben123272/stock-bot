import requests
import yfinance as yf
from flask import Flask, request
from threading import Thread
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# הגדרות
BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5a0PnXRbbbS-jdPnn3BZfM"
CHAT_ID = "8253548607"
MY_STOCKS = ["MU", "SNDK", "MRVL", "CRDO", "TSEM", "MP", "IREN", "OKLO", "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG", "PLTR"]
GOLD_POOL = ["QQQ", "SOXX", "XLE", "GS", "JPM", "NFLX", "COST", "V", "AAPL", "AMZN"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except: pass

def get_action_advice(data):
    if data['bb'] == "קרוב לתמיכה 🟢" and data['macd'] == "מומנטום חיובי 🚀":
        return "💡 **המלצה:** קנייה / כניסה לפוזיציה"
    elif data['bb'] == "קרוב להתנגדות 🔴":
        return "💡 **המלצה:** זהירות / שקול מימוש רווחים"
    elif data['trend'] == "שורי (Bullish)" and data['rs'] == "מכה את השוק 🚀":
        return "💡 **המלצה:** החזק - מומנטום חזק"
    return "💡 **המלצה:** המתנה / מעקב בלבד"

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        if len(hist) < 26: return None
        curr = hist['Close'].iloc[-1]
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        std_20 = hist['Close'].rolling(window=20).std().iloc[-1]
        bb = "קרוב לתמיכה 🟢" if curr <= (sma_20 - std_20*2) else ("קרוב להתנגדות 🔴" if curr >= (sma_20 + std_20*2) else "נייטרלי ➖")
        exp1 = hist['Close'].ewm(span=12).mean().iloc[-1]
        exp2 = hist['Close'].ewm(span=26).mean().iloc[-1]
        macd = "מומנטום חיובי 🚀" if exp1 > exp2 else "מומנטום שלילי 📉"
        atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
        rr = (atr * 3) / (atr * 1.5)
        data = {"ticker": ticker, "price": f"{curr:.2f}$", "macd": macd, "bb": bb, "rr": f"1:{rr:.1f}", "trend": "שורי (Bullish)" if curr > sma_20 else "דובי (Bearish)"}
        data["advice"] = get_action_advice(data)
        return data
    except: return None

def generate_full_report():
    my_results = [analyze_stock(t) for t in MY_STOCKS if analyze_stock(t)]
    gold = sorted([analyze_stock(t) for t in GOLD_POOL if analyze_stock(t)], key=lambda x: x['rr'], reverse=True)[:2]
    report = f"🏛️ **דוח אלגוטריידינג מוסדי - {datetime.now().strftime('%d/%m/%Y')}**\n\n"
    report += "🌟 **מניות זהב חיצוניות:**\n" + "\n".join([f"• {g['ticker']} | {g['price']}" for g in gold]) + "\n\n"
    report += "📊 **16 המניות שלך:**\n" + "\n".join([f"📌 {d['ticker']} ({d['price']}) - {d['advice']}" for d in my_results])
    return report

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and update["message"].get("text") == "סקירה":
        send_telegram_message("⏳ מנתח עבורך נתונים...")
        send_telegram_message(generate_full_report())
    return "OK"

def scheduler():
    while True:
        # בדיקה לשעה 20:00 (שעון השרת הוא בד"כ UTC, אז 17:00 UTC = 20:00 ישראל)
        if datetime.utcnow().hour == 17 and datetime.utcnow().minute == 0:
            send_telegram_message(generate_full_report())
            time.sleep(65)
        time.sleep(30)

if __name__ == "__main__":
    Thread(target=scheduler).start()
    app.run(host='0.0.0.0', port=10000)
