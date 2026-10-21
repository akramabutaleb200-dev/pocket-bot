import os
import requests
import pandas as pd
import yfinance as yf

# جلب الإعدادات السرية من بيئة التشغيل (نفس الأسماء الأصلية)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# قائمة بأقوى أزواج العملات ذات العائد الأعلى (+85%) دائماً
FOREX_PAIRS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD"
}

def fetch_data(ticker):
    """جلب بيانات السعر الحية لدقيقة واحدة"""
    try:
        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30:
            return None
        return df
    except:
        return None

def analyze_strategy(df):
    """تحليل السوق بواسطة 7 مؤشرات فنية مدمجة لصفقات الدقيقة الواحدة"""
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    
    # 1. المتوسطات المتحركة الأسية (EMA 9 & EMA 21)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    
    # 2. مؤشر القوة النسبية (RSI 14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # 3. مؤشر ستوكاستيك (Stochastic 14, 3, 3)
    low_14 = low.rolling(window=14).min()
    high_14 = high.rolling(window=14).max()
    k_percent = 100 * ((close - low_14) / (high_14 - low_14))
    d_percent = k_percent.rolling(window=3).mean()
    
    # 4. مؤشر الماكد (MACD 12, 26, 9)
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    
    # 5. حدود بولينجر (Bollinger Bands 20, 2)
    ma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    upper_band = ma20 + (std20 * 2)
    lower_band = ma20 - (std20 * 2)
    
    # 6. مؤشر قناة السلع (CCI 14)
    tp = (high + low + close) / 3
    cci = (tp - tp.rolling(14).mean()) / (0.015 * tp.rolling(14).std())
    
    # القيم الحالية (آخر شمعة مغلقة)
    c_rsi = rsi.iloc[-1]
    c_k = k_percent.iloc[-1]
    c_d = d_percent.iloc[-1]
    c_macd = macd.iloc[-1]
    c_sig = signal_line.iloc[-1]
    c_close = close.iloc[-1]
    c_upper = upper_band.iloc[-1]
    c_lower = lower_band.iloc[-1]
    c_cci = cci.iloc[-1]
    
    # شروط دخول صفقة شراء (CALL) قوية جداً باتفاق المؤشرات
    call_condition = (
        (ema9.iloc[-1] > ema21.iloc[-1]) and   
        (c_rsi < 40) and                        
        (c_k > c_d and c_k < 30) and            
        (c_macd > c_sig) and                    
        (c_close <= c_lower * 1.0005) and       
        (c_cci < -100)                          
    )
    
    # شروط دخول صفقة بيع (PUT) قوية جداً باتفاق المؤشرات
    put_condition = (
        (ema9.iloc[-1] < ema21.iloc[-1]) and   
        (c_rsi > 60) and                        
        (c_k < c_d and c_k > 70) and            
        (c_macd < c_sig) and                    
        (c_close >= c_upper * 0.9995) and       
        (c_cci > 100)                           
    )
    
    if call_condition:
        return "CALL (شراء) 🟢"
    elif put_condition:
        return "PUT (بيع) 🔴"
    return None

def send_signal(pair, action, expiry):
    """دالة إرسال الإشارة المتوافقة تماماً مع الهيكل الأصلي للمسجات"""
    message = f"🚨 **إشارة تداول جديدة (+90%)** 🚨\n\n" \
              f"📊 الأصول: {pair}\n" \
              f"📈 الاتجاه: {action}\n" \
              f"⏳ مدة الصفقة: {expiry}\n" \
              f"🏛 المنصة: Pocket Option\n" \
              f"⚠️ تنبيه: ادخل فوراً بدون مضاعفات!"
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
        print(f"تم إرسال إشارة: {pair} - {action}")
    except Exception as e:
        print(f"خطأ في إرسال الإشارة: {e}")

def main():
    print("البوت يعمل الآن ويراقب السوق...")
    for ticker, pair_name in FOREX_PAIRS.items():
        data = fetch_data(ticker)
        if data is not None:
            signal = analyze_strategy(data)
            if signal:
                # استدعاء دالة الإرسال مع تثبيت مدة الصفقة على 1 MIN كطلبك
                send_signal(pair_name, signal, "1 MIN")
                break 

if __name__ == "__main__":
    main()
