import time
import schedule
import pandas as pd
import yfinance as yf
import telebot

# הגדרות בוט ומקבלים
TELEGRAM_BOT_TOKEN = "8710966476:AAEEMZiiTBNWxrBYFmo3mK_eOGDAUZWaZis"
TELEGRAM_CHAT_IDS = ["8253548607"]  # ניתן להוסיף כאן עוד מזהים בעתיד

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# 16 המניות שנבחרו למעקב שוטף
WATCHLIST = [
    "MU", "SNDK", "MRVL", "CRDO", "TSEM", "COHR", "MP", 
    "IREN", "OKLO", "VECO", "IBM", "GOOGL", "AMD", "META", "NVDA", "CEG"
]

# מאגר לסריקת הזדמנויות חדשות
DISCOVERY_POOL = ["SPY", "QQQ", "AMZN", "MSFT", "TSLA", "AVGO", "ARM", "SMCI", "PLTR", "INSP"]

def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="60d", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None
        
        close = df['Close']
        ema10 = close.ewm(span=10, adjust=False).mean()
        ema20 = close.ewm(span=20, adjust=False).mean()
        
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        curr_price = float(close.iloc[-1])
        curr_ema10 = float(ema10.iloc[-1])
        curr_ema20 = float(ema20.iloc[-1])
        curr_rsi = float(rsi.iloc[-1])
        
        return {
            "price": curr_price,
            "ema10": curr_ema10,
            "ema20": curr_ema20,
            "rsi": curr_rsi
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def send_to_all(message):
    for chat_id in TELEGRAM_CHAT_IDS:
        try:
            bot.send_message(chat_id, message, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def run_daily_scan():
    print("Starting daily scan...")
    report = "📊 *דו״ח סקירה יומי - שוק ההון*\n\n"
    
    # 1. סקירת רשימת המעקב (16 מניות)
    report += "*סטטוס פוזיציות קיימות:*\n"
    for ticker in WATCHLIST:
        data = analyze_ticker(ticker)
        if data:
            if data["ema10"] > data["ema20"] and data["rsi"] > 50:
                status = "🟢 להישאר (מגמה חיובית)"
            else:
                status = "🔴 לשקול יציאה (חולשה טכנית)"
            report += f"• *{ticker}*: {status} (${data['price']:.2f})\n"
        else:
            report += f"• *{ticker}*: ⚠️ שגיאה בשליפת נתונים\n"
            
    # 2. איתור 2 הזדמנויות חדשות
    report += "\n🎯 *2 הזדמנויות כניסה חדשות להיום:*\n"
    opportunities = []
    
    for ticker in DISCOVERY_POOL:
        data = analyze_ticker(ticker)
        if data and data["ema10"] > data["ema20"] and 50 < data["rsi"] < 70:
            score = data["rsi"]
            opportunities.append((ticker, score, data["price"]))
            
    opportunities.sort(key=lambda x: x[1], reverse=True)
    top_2 = opportunities[:2]
    
    if top_2:
        for ticker, rsi, price in top_2:
            report += f"• *{ticker}*: איתות קנייה חזק (מחיר: ${price:.2f}, RSI: {rsi:.1f})\n"
    else:
        report += "לא נמצאו איתותים חדשים ברמת דיוק גבוהה היום.\n"
        
    send_to_all(report)
    print("Scan complete and report sent.")

# תזמון הרצה יומית ב-20:00 (שעון ישראל)
schedule.every().day.at("17:00").do(run_daily_scan)

send_to_all("🤖 *הבוט הופעל בהצלחה ב-Render!* הסריקה היומית מתוזמנת לשעה 20:00.")

while True:
    schedule.run_pending()
    time.sleep(60)
