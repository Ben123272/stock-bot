import requests
import yfinance as yf
from flask import Flask, request
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)

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

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        spy = yf.Ticker("SPY").history(period="60d")
        if len(hist) < 26 or len(spy) < 20: return None
        curr = hist['Close'].iloc[-1]
        sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
        std_20 = hist['Close'].rolling(window=20).std().iloc[-1]
        upper_band = sma_20 + (std_20 * 2)
        lower_band = sma_20 - (std_20 * 2)
        bb_status = "קרוב לתמיכה 🟢" if curr <= lower_band * 1.02 else ("קרוב להתנגדות 🔴" if curr >= upper_band * 0.98 else "בתוך הרצועות ➖")
        
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        macd_status = "מומנטום חיובי 🚀" if macd.iloc[-1] > signal.iloc[-1] else "מומנטום שלילי 📉"
        
        atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
        stop_loss = curr - (atr * 1.5)
        take_profit = curr + (atr * 3)
        risk = curr - stop_loss
        reward = take_profit - curr
        rr = reward / risk if risk > 0 else 0
        
        trend = "שורי (Bullish)" if curr > sma_20 else "דובי (Bearish)"
        return {
            "ticker": ticker, "price": f"{curr:.2f}$", "trend": trend,
            "macd": macd_status, "bb": bb_status, "rr": f"1:{rr:.1f}",
            "score": rr if trend == "שורי (Bullish)" else 0
        }
    except: return None

def generate_full_report():
    today = datetime.now().strftime('%Y-%m-%d')
    my_results = [analyze_stock(t) for t in MY_STOCKS if analyze_stock(t)]
    gold_results = sorted([analyze_stock(t) for t in GOLD_POOL if analyze_stock(t)], key=lambda x: x['score'], reverse=True)[:2]
    
    report = f"🏛️ **דוח אלגוטריידינג מוסדי - {today}**\n\n"
    report += "🌟 **הזדמנויות הזהב:**\n" + "\n".join([f"• {g['ticker']} ({g['price']}) | R/R: {g['rr']}" for g in gold_results]) + "\n\n"
    report += "📊 **16 המניות שלך:**\n" + "\n".join([f"📌 {d['ticker']} ({d['price']}) | {d['trend']} | {d['bb']}" for d in my_results])
    return report

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update:
        msg = update["message"].get("text", "").strip()
        if msg == "סקירה":
            send_telegram_message("⏳ מכין דוח מניות מלא...")
            send_telegram_message(generate_full_report())
    return "OK"

def scheduled_job():
    while True:
        if datetime.utcnow().hour == 17 and datetime.utcnow().minute == 0:
            send_telegram_message(generate_full_report())
            time.sleep(65)
        time.sleep(30)

@app.route('/')
def home():
    return "Bot Webhook is active!"

if __name__ == "__main__":
    Thread(target=scheduled_job).start()
    app.run(host='0.0.0.0', port=10000)
