import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread
import time
from datetime import datetime

app = Flask(__name__)

# הגדרות המערכת שלך
BOT_TOKEN = "8710966476:AAH_Sf7G2HIuy5a0PnXRbbbS-jdPnn3BZfM"
CHAT_ID = "8253548607"
STOCKS_LIST = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error: {e}")

def get_sentiment(stock):
    """סריקת חדשות וניתוח סנטימנט אוטומטי (NLP)"""
    try:
        news = stock.news
        if not news: return "נייטרלי ➖"
        score = sum(1 for item in news[:5] if any(w in item.get('title', '').lower() for w in ['up', 'surge', 'beat', 'growth', 'rally', 'buy']))
        score -= sum(1 for item in news[:5] if any(w in item.get('title', '').lower() for w in ['down', 'drop', 'miss', 'crash', 'loss', 'sell']))
        return "חיובי 🟢" if score > 0 else ("שלילי 🔴" if score < 0 else "נייטרלי ➖")
    except:
        return "לא זמין ❓"

def ultimate_institutional_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="60d")
        spy = yf.Ticker("SPY").history(period="60d")
        info = stock.info
        
        if len(hist) < 26 or len(spy) < 20: return None
            
        curr = hist['Close'].iloc[-1]
        
        # 1. מדדים טכניים מתקדמים (SMA, Bollinger Bands, MACD)
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

        # 2. ניהול סיכונים מתקדם (ATR & Risk/Reward Ratio)
        atr = (hist['High'] - hist['Low']).rolling(window=14).mean().iloc[-1]
        stop_loss = curr - (atr * 1.5)
        take_profit = curr + (atr * 3)
        risk = curr - stop_loss
        reward = take_profit - curr
        risk_reward_ratio = reward / risk if risk > 0 else 0

        # 3. פונדמנטליים ועוצמה מול השוק (S&P 500)
        pe = info.get('forwardPE', 'N/A')
        stock_ret = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
        spy_ret = (spy['Close'].iloc[-1] - spy['Close'].iloc[0]) / spy['Close'].iloc[0]
        rs = "מכה את השוק 🚀" if stock_ret > spy_ret else "חלש מהשוק 📉"
        
        trend = "שורי (Bullish)" if curr > sma_20 else "דובי (Bearish)"
        sentiment = get_sentiment(stock)
        
        # ציון משוקלל לטובת מציאת ההזדמנות הטובה ביותר בדוח
        score_val = risk_reward_ratio if trend == "שורי (Bullish)" else 0

        return {
            "ticker": ticker, "price": f"{curr:.2f}$", "trend": trend, "pe": pe,
            "rs": rs, "sentiment": sentiment, "macd": macd_status, "bb": bb_status,
            "sl": f"{stop_loss:.2f}$", "tp": f"{take_profit:.2f}$", "rr": f"1:{risk_reward_ratio:.1f}",
            "score": score_val
        }
    except Exception as e:
        print(f"Error {ticker}: {e}")
        return None

def job():
    today = datetime.now().strftime('%Y-%m-%d')
    results = []
    
    for ticker in STOCKS_LIST:
        data = ultimate_institutional_analysis(ticker)
        if data:
            results.append(data)
            
    if not results:
        return

    # בחירת ההזדמנות המובילה היום (דובדבן שבקצפת)
    best_stock = max(results, key=lambda x: x['score']) if results else None

    report = f"🏛️ **דוח אלגוטריידינג מוסדי מלא - {today}**\n"
    if best_stock and best_stock['score'] > 0:
        report += f"⭐ **ההזדמנות החמה היום:** {best_stock['ticker']} (יחס R/R: {best_stock['rr']})\n"
    report += "-----------------------------------\n\n"
    
    for data in results:
        report += f"📌 **{data['ticker']}** ({data['price']})\n"
        report += f"• מגמה: {data['trend']} | P/E: {data['pe']}\n"
        report += f"• MACD: {data['macd']}\n"
        report += f"• בולינגר: {data['bb']}\n"
        report += f"• מול השוק: {data['rs']} | חדשות: {data['sentiment']}\n"
        report += f"• 🛑 SL: {data['sl']} | 🎯 TP: {data['tp']} (יחס R/R: {data['rr']})\n\n"
        
    send_telegram_message(report)

@app.route('/')
def home():
    return "Ultimate Institutional Quant Bot is Online & Fully Loaded!"

def run_scheduler():
    while True:
        job()
        time.sleep(86400) # ריצה כל 24 שעות

if __name__ == "__main__":
    Thread(target=run_scheduler).start()
    app.run(host='0.0.0.0', port=10000)
