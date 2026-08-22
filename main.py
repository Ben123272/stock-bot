import requests
import yfinance as yf
from flask import Flask
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)

# הגדרות הטלגרם שלך
BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5a0PnXRbbbS-jdPnn3BZfM"
CHAT_ID = "8253548607"

# 16 המניות המדויקות שלך
MY_STOCKS = [
    "MU", "SNDK", "MRVL", "CRDO", "TSEM", "MP", "IREN", "OKLO", 
    "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG", "PLTR"
]

# מאגר חיצוני לסריקת שתי מניות "זהב" נוספות
GOLD_POOL = ["QQQ", "SOXX", "XLE", "GS", "JPM", "NFLX", "COST", "V", "AAPL", "AMZN"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def get_sentiment(stock):
    try:
        news = stock.news
        if not news: return "נייטרלי ➖"
        score = sum(1 for item in news[:5] if any(w in item.get('title', '').lower() for w in ['up', 'surge', 'beat', 'growth', 'rally', 'buy']))
        score -= sum(1 for item in news[:5] if any(w in item.get('title', '').lower() for w in ['down', 'drop', 'miss', 'crash', 'loss', 'sell']))
        return "חיובי 🟢" if score > 0 else ("שלילי 🔴" if score < 0 else "נייטרלי ➖")
    except:
        return "לא זמין ❓"

def get_action_advice(data):
    """מנוע החלטות: כותב לך בדיוק מה לעשות לפי המדדים"""
    if data['bb'] == "קרוב לתמיכה 🟢" and data['macd'] == "מומנטום חיובי 🚀":
        return "💡 **המלצה:** קנייה / כניסה לפוזיציה (מומנטום שורי בתמיכה)"
    elif data['bb'] == "קרוב להתנגדות 🔴":
        return "💡 **המלצה:** זהירות / שקול מימוש רווחים (קרוב להתנגדות עליונה)"
    elif data['trend'] == "שורי (Bullish)" and data['rs'] == "מכה את השוק 🚀":
        return "💡 **המלצה:** החזק / מגמת עליות חזקה המכה את המדד"
    else:
        return "💡 **המלצה:** המתנה / מעקב בלבד (אין טריגר ברור)"

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        spy = yf.Ticker("SPY").history(period="60d")
        info = stock.info
        
        if len(hist) < 26 or len(spy) < 20: return None
            
        curr = hist['Close'].iloc[-1]
        
        # מדדים טכניים (SMA, Bollinger, MACD)
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

        # ניהול סיכונים (ATR & RR)
        atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
        stop_loss = curr - (atr * 1.5)
        take_profit = curr + (atr * 3)
        risk = curr - stop_loss
        reward = take_profit - curr
        risk_reward_ratio = reward / risk if risk > 0 else 0

        pe = info.get('forwardPE', 'N/A')
        stock_ret = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
        spy_ret = (spy['Close'].iloc[-1] - spy['Close'].iloc[0]) / spy['Close'].iloc[0]
        rs = "מכה את השוק 🚀" if stock_ret > spy_ret else "חלש מהשוק 📉"
        trend = "שורי (Bullish)" if curr > sma_20 else "דובי (Bearish)"
        sentiment = get_sentiment(stock)

        data = {
            "ticker": ticker, "price": f"{curr:.2f}$", "trend": trend, "pe": pe,
            "rs": rs, "sentiment": sentiment, "macd": macd_status, "bb": bb_status,
            "sl": f"{stop_loss:.2f}$", "tp": f"{take_profit:.2f}$", "rr": f"1:{risk_reward_ratio:.1f}",
            "score": risk_reward_ratio if trend == "שורי (Bullish)" else 0
        }
        
        data["advice"] = get_action_advice(data)
        return data
    except Exception as e:
        print(f"Error {ticker}: {e}")
        return None

def generate_full_report():
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 1. סריקת 16 המניות שלך
    my_results = []
    for ticker in MY_STOCKS:
        res = analyze_stock(ticker)
        if res: my_results.append(res)
        
    # 2. סריקת מאגר הזהב למציאת 2 המניות המובילות החיצוניות
    gold_results = []
    for ticker in GOLD_POOL:
        res = analyze_stock(ticker)
        if res: gold_results.append(res)
    gold_results.sort(key=lambda x: x['score'], reverse=True)
    top_gold = gold_results[:2]

    # 3. בניית הדו"ח המלא
    report = f"🏛️ **דוח אלגוטריידינג מוסדי מלא - {today}**\n"
    report += "===================================\n\n"
    
    report += "🌟 **הזדמנויות הזהב המובילות בשוק (מחוץ לרשימה):**\n"
    for g in top_gold:
        report += f"• **{g['ticker']}** ({g['price']}) | יחס R/R: {g['rr']} | {g['trend']}\n"
    report += "\n-----------------------------------\n\n"
    
    report += "📊 **סקירת 16 המניות שלך והנחיות פעולה:**\n\n"
    for data in my_results:
        report += f"📌 **{data['ticker']}** ({data['price']})\n"
        report += f"• מגמה: {data['trend']} | P/E: {data['pe']}\n"
        report += f"• MACD: {data['macd']} | בולינגר: {data['bb']}\n"
        report += f"• מול השוק: {data['rs']} | חדשות: {data['sentiment']}\n"
        report += f"• 🛑 SL: {data['sl']} | 🎯 TP: {data['tp']} (R/R: {data['rr']})\n"
        report += f"{data['advice']}\n\n"
        
    return report

def bot_listener():
    """הלולאה שמאזינת לטלגרם ומחכה שתכתוב 'סקירה'"""
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}"
            resp = requests.get(url).json()
            if resp.get("result"):
                for update in resp["result"]:
                    last_update_id = update["update_id"]
                    msg = update.get("message", {}).get("text", "").strip()
                    if msg == "סקירה":
                        send_telegram_message("⏳ מכין עבורך סקירה עדכנית לכל 16 המניות ומאגר הזהב... מיד אצלך!")
                        report = generate_full_report()
                        send_telegram_message(report)
        except Exception as e:
            print(f"Listener Error: {e}")
        time.sleep(3)

def scheduled_job():
    """תזמון אוטומטי לשעה 20:00 בדיוק שעון ישראל (17:00 UTC)"""
    while True:
        now = datetime.utcnow()
        if now.hour == 17 and now.minute == 0:
            report = generate_full_report()
            send_telegram_message(report)
            time.sleep(65)
        time.sleep(30)

@app.route('/')
def home():
    return "Full Institutional Quant Bot with Listener is Online!"

if __name__ == "__main__":
    Thread(target=bot_listener).start()
    Thread(target=scheduled_job).start()
    app.run(host='0.0.0.0', port=10000)
