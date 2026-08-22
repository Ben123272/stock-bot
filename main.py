import os
import yfinance as yf
import requests
from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5aOPnXRbbbS-jdPnn3BZfM"
MY_STOCKS = ["MU", "SNDK", "MRVL", "CRDO", "TSEM", "MP", "IREN", "OKLO", "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG", "PLTR", "COHR"]

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1.5mo")
        if hist.empty: return None
        price = hist['Close'].iloc[-1]
        sma = hist['Close'].rolling(window=20).mean().iloc[-1]
        trend = "עלייה" if price > sma else "ירידה"
        
        # מומנטום פשוט לפי ממוצע 12
        momentum_val = hist['Close'].rolling(window=12).mean().iloc[-1]
        macd = "חיובי" if price > momentum_val else "שלילי"
        
        # סטטוס לתיק הקיים
        action = "להישאר 🟢" if (trend == "עלייה" and macd == "חיובי") else "לצאת 🔴"
        return {'ticker': ticker, 'price': f"{price:.2f}$", 'trend': trend, 'macd': macd, 'action': action}
    except:
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    global MY_STOCKS
    update = request.get_json()
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        msg = update["message"].get("text", "").strip()
        
        # פקודת החלפה
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
                send_telegram_message(chat_id, "פורמט לא תקין. נסה: 'החלף TSEM ב-NOW'")

        elif msg == "סקירה":
            send_telegram_message(chat_id, "⏳ מעדכן דוח מניות...")
            report = "📈 **דוח מניות (התיק שלך):**\n" + "\n".join([f"• {s}: {analyze_stock(s)['action']}" if analyze_stock(s) else f"• {s}: שגיאה" for s in MY_STOCKS])
            send_telegram_message(chat_id, report)
            
        elif msg.startswith("בדוק "):
            ticker = msg.split(" ")[1].upper()
            send_telegram_message(chat_id, f"🔍 מנתח לעומק את {ticker}...")
            
            res = analyze_stock(ticker)
            if res:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="60d")
                curr = hist['Close'].iloc[-1]
                atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
                
                stop_loss = curr - (atr * 1.5)
                risk = curr - stop_loss
                take_profit = curr + (risk * 3)  # יחס 1:3 מדויק
                actual_rr = 3.0
                
                # 3 רמות החלטה למניה חדשה
                if res['trend'] == "עלייה" and res['macd'] == "חיובי":
                    recommendation = "✅ **המלצה: להיכנס (שווה כניסה)**\n🚀 המגמה והמומנטום חיוביים ותומכים במהלך."
                elif res['trend'] == "עלייה" and res['macd'] == "שלילי":
                    recommendation = "⏳ **המלצה: להמתין קצת**\n⚠️ המגמה הראשית עולה, אבל המומנטום כרגע בתיקון/חולשה קצרה. עדיף לחכות שיתייצב."
                elif res['trend'] == "ירידה" and res['macd'] == "חיובי":
                    recommendation = "⏳ **המלצה: להמתין קצת**\n🔄 יש סימני מומנטום ראשוניים, אבל המגמה עדיין יורדת. כדאי להמתין לפריצת ממוצע."
                else:
                    recommendation = "❌ **המלצה: לא להיכנס בכלל**\n🛑 גם המגמה וגם המומנטום שליליים. סיכון גבוה מדי."

                reply = (
                    f"🎯 **ניתוח מעמיק ל-{ticker}**\n\n"
                    f"💰 מחיר נוכחי: {res['price']}\n"
                    f"📈 מגמה (SMA20): {res['trend']}\n"
                    f"🚀 מומנטום: {res['macd']}\n"
                    f"⚖️ יחס סיכון/סיכוי (R/R): 1:{actual_rr:.1f}\n\n"
                    f"{recommendation}\n\n"
                    f"🛑 סטופ לוס מוצע: {stop_loss:.2f}$\n"
                    f"🎯 טייק פרופיט מוצע: {take_profit:.2f}$"
                )
                send_telegram_message(chat_id, reply)
            else:
                send_telegram_message(chat_id, f"❌ לא הצלחתי למצוא נתונים עבור {ticker}.")
                
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
