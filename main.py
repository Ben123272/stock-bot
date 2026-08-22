import os
import yfinance as yf
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5aOPnXRbbbS-jdPnn3BZfM"
# הרשימה שלך
MY_STOCKS = ["MU", "SNDK", "MRVL", "CRDO", "TSEM", "MP", "IREN", "OKLO", "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG", "PLTR", "COHR"]

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
        action = "להישאר 🟢" if (trend == "עלייה" and macd == "חיובי") else "לצאת 🔴"
        return {'ticker': ticker, 'price': f"{price:.2f}$", 'action': action}
    except:
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    global MY_STOCKS
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        msg = update["message"].get("text", "").strip()
        
        # פקודת החלפה: "החלף MU ב-NOW"
        if msg.startswith("החלף "):
            try:
                parts = msg.split(" ")
                old_ticker = parts[1].upper()
                new_ticker = parts[3].upper()
                if old_ticker in MY_STOCKS:
                    MY_STOCKS.remove(old_ticker)
                    MY_STOCKS.append(new_ticker)
                    send_telegram_message(chat_id, f"✅ הוחלפה: {old_ticker} הוסרה, {new_ticker} התווספה לרשימה.")
                else:
                    send_telegram_message(chat_id, f"❌ המניה {old_ticker} לא נמצאה ברשימה.")
            except:
                send_telegram_message(chat_id, "פורמט לא תקין. נסה: 'החלף MU ב-NOW'")

        elif msg == "סקירה":
            send_telegram_message(chat_id, "⏳ מעדכן דוח מניות...")
            report = "📈 **דוח מניות:**\n" + "\n".join([f"• {s}: {analyze_stock(s)['action']}" for s in MY_STOCKS if analyze_stock(s)])
            send_telegram_message(chat_id, report)
            
        elif msg.startswith("בדוק "):
            # (כאן נשאר אותו קוד ניתוח ממוקד)
            ticker = msg.split(" ")[1].upper()
            res = analyze_stock(ticker)
            if res:
                send_telegram_message(chat_id, f"🎯 {ticker}: {res['price']} | {res['action']}")
                
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
