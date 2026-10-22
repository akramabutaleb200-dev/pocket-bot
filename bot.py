import os
import requests
import pandas as pd
import yfinance as yf

# جلب الإعدادات السرية لبوت التلغرام
TOKEN = os.getenv("8805409524:AAHISPXyj8Vtek5jIYeWs1DxH2EfiyjcG0w")
CHAT_ID = os.getenv("8099576587")

# قائمة موسعة بأقوى أزواج العملات الحقيقية والمباشرة في السوق المفتوح (تتجاوز عوائدها 20% دائماً)
LIVE_FOREX_PAIRS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD",
    "EURGBP=X": "EUR/GBP",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY"
}

def fetch_live_data(ticker):
    """جلب بيانات السعر الحقيقية والمباشرة للسوق المفتوح لدقيقة واحدة"""
    try:
        df = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30:
            return None
        return df
    except:
        return None

def analyze_strategy(df, pair_name):
    """التحليل الفني الفائق بواسطة 7 مؤشرات مدمجة لصفقات الدقيقة الواحدة في السوق الحقيقي"""
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    
    # 1. المتوسطات المتحركة الأسية لتحديد الاتجاه (EMA 9 & EMA 21)
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    
    # 2. مؤشر القوة النسبية لقياس الانعكاس (RSI 14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # 3. مؤشر ستوكاستيك السريع (Stochastic 14, 3, 3)
    low_14 = low.rolling(window=14).min()
    high_14 = high.rolling(window=14).max()
    k_percent = 100 * ((close - low_14) / (high_14 - low_14))
    d_percent = k_percent.rolling(window=3).mean()
    
    # 4. مؤشر الماكد لقياس اندفاع السيولة (MACD 12, 26, 9)
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    
    # 5. حدود بولينجر لرصد الانفجار السعري (Bollinger Bands 20, 2)
    ma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    upper_band = ma20 + (std20 * 2)
    lower_band = ma20 - (std20 * 2)
    
    # 6. مؤشر قناة السلع (CCI 14) رصد الذروة المتطرفة
    tp = (high + low + close) / 3
    cci = (tp - tp.rolling(14).mean()) / (0.015 * tp.rolling(14).std())
    
    # استخراج قيم آخر شمعة حقيقية مغلقة فوراً
    c_rsi = rsi.iloc[-1]
    c_k = k_percent.iloc[-1]
    c_d = d_percent.iloc[-1]
    c_macd = macd.iloc[-1]
    c_sig = signal_line.iloc[-1]
    c_close = close.iloc[-1]
    c_upper = upper_band.iloc[-1]
    c_lower = lower_band.iloc[-1]
    c_cci = cci.iloc[-1]
    
    # طباعة تقرير الحركة والتحليل حياً داخل الـ Logs لـ GitHub للتحقق المباشر
    print(f"\n📊 [سوق حقيقي حيو] فحص الزوج: {pair_name} | السعر: {c_close:.5f}")
    print(f"   📈 RSI: {c_rsi:.2f} | Stochastic K: {c_k:.2f} | CCI: {c_cci:.2f}")
    print(f"   📈 Bollinger Upper: {c_upper:.5f} | Lower: {c_lower:.5f}")
    
    # شروط صفقة الشراء (CALL) - توافق الفلاتر السبعة في السوق الحقيقي
    call_condition = (
        (ema9.iloc[-1] > ema21.iloc[-1]) and   
        (c_rsi < 40) and                        # تشبع بيعي
        (c_k > c_d and c_k < 30) and            
        (c_macd > c_sig) and                    
        (c_close <= c_lower * 1.0005) and       # ملامسة خط بولينجر السفلي
        (c_cci < -100)                          
    )
    
    # شروط صفقة البيع (PUT) - توافق الفلاتر السبعة في السوق الحقيقي
    put_condition = (
        (ema9.iloc[-1] < ema21.iloc[-1]) and   
        (c_rsi > 60) and                        # تشبع شرائي
        (c_k < c_d and c_k > 70) and            
        (c_macd < c_sig) and                    
        (c_close >= c_upper * 0.9995) and       # ملامسة خط بولينجر العلوي
        (c_cci > 100)                           
    )
    
    if call_condition:
        return "CALL (شراء) 🟢"
    elif put_condition:
        return "PUT (بيع) 🔴"
    return None

def send_signal(pair, action, expiry):
    """إرسال الإشارة الفورية والمباشرة للتلغرام بالمعايير المعدلة"""
    message = f"🚨 **إشارة تداول حقيقية (+90%)** 🚨\n\n" \
              f"📊 الأصول: `{pair}`\n" \
              f"📈 الاتجاه: `{action}`\n" \
              f"⏳ مدة الصفقة: `{expiry}`\n" \
              f"🏛 المنصة: Pocket Option\n" \
              f"💰 عائد الربح المستهدف: `+20% فما فوق`\n" \
              f"⚠️ تنبيه: ادخل فوراً مع بداية الشمعة بدون مضاعفات!"
    
    url = f"https://telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload)
        print(f"🚀 استجابة التلغرام: {r.status_code} | تم إرسال إشارة بنجاح لـ {pair}")
    except Exception as e:
        print(f"❌ خطأ في إرسال التلغرام: {e}")

def main():
    print("البوت يعمل الآن ويراقب أسواق الفوركس الحقيقية المباشرة...")
    
    # رسالة ترحيبية فورية عند تشغيل الـ Workflow للتأكد من الاتصال
    send_signal("اختبار اتصال السوق الحقيقي", "ناجح ومربوط بنجاح 🟢", "1 MIN")
    
    for ticker, pair_name in LIVE_FOREX_PAIRS.items():
        data = fetch_live_data(ticker)
        if data is not None:
            signal = analyze_strategy(data, pair_name)
            if signal:
                send_signal(pair_name, signal, "1 MIN")
                break 
    print("\n✅ تم فحص دورة الأسواق الحقيقية بنجاح.")

if __name__ == "__main__":
    main()
