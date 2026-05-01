import pandas as pd
import numpy as np
import requests 
import joblib 
from tensorflow.keras.models import load_model
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import time
import json
from datetime import datetime, timedelta

SUPPORTED_ASSETS = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "Cardano": "cardano",
    "Dogecoin": "dogecoin",
    "Avalanche": "avalanche-2",
    "Polkadot": "polkadot",     
    "Shiba Inu": "shiba-inu"    
}
LOOK_BACK = 60 
NEWS_API_KEY = "77d8bea3b7d44301add752af50c244c2" 
NEWS_QUERY = "bitcoin OR ethereum OR solana OR binance OR cryptocurrency" 

LOCK_FILE = "signal_lock.json"
LOCK_DURATION_HOURS = 4  


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_live_price(coin_id):
    URL = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    try:
        response = requests.get(URL, timeout=10)
        if response.status_code == 429:
            return None 
        response.raise_for_status()
        data = response.json()
        return data[coin_id]['usd']
    except Exception:
        return None

def fetch_news_sentiment(api_key, query):
    URL = "https://newsapi.org/v2/everything"
    params = {'q': query, 'apiKey': api_key, 'sortBy': 'publishedAt', 'language': 'en', 'pageSize': 20}
    try:
        response = requests.get(URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        headlines = [article['title'] for article in data.get('articles', []) if article.get('title')]
        if not headlines: return 0.0, []
        analyzer = SentimentIntensityAnalyzer()
        scores = [analyzer.polarity_scores(h)['compound'] for h in headlines]
        return sum(scores) / len(scores), headlines
    except Exception:
        return 0.0, []

def predict_and_advise(coin_id, look_back=LOOK_BACK):
   
    try:
        LSTM_MODEL = load_model(f'models/lstm_model_{coin_id}.h5')
        SCALER = joblib.load(f'models/scaler_{coin_id}.pkl')
        df = pd.read_csv(f'data/{coin_id}_historical_prices.csv', index_col='timestamp', parse_dates=True)
    except Exception:
        return 0, 0, 0, 0, "Model Error", "HIGH", [], 0, 0, "Check Files", 0

   
    df['RSI'] = calculate_rsi(df['Price'])
    df['EMA20'] = df['Price'].ewm(span=20, adjust=False).mean()
    
    current_rsi = df['RSI'].iloc[-1]
    current_ema = df['EMA20'].iloc[-1]

   
    current_price = get_live_price(coin_id)
    if current_price is None:
        current_price = df['Price'].iloc[-1]

   
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                lock_data = json.load(f)
            
         
            if lock_data.get('coin_id') == coin_id:
                last_time = datetime.strptime(lock_data['time'], "%Y-%m-%d %H:%M:%S")
                time_diff = datetime.now() - last_time
                
     
                if time_diff < timedelta(hours=LOCK_DURATION_HOURS):
                    saved_advice = lock_data['advice']
                    saved_tp = lock_data['tp']
                    saved_sl = lock_data['sl']
                    
           
                    break_lock = False
                    if "BUY" in saved_advice and (current_price >= saved_tp or current_price <= saved_sl):
                        break_lock = True
                    elif "SELL" in saved_advice and (current_price <= saved_tp or current_price >= saved_sl):
                        break_lock = True
                    
                    if not break_lock:
                        print(f"🔒 Signal Locked for {coin_id} (Valid till {last_time + timedelta(hours=LOCK_DURATION_HOURS)})")
                   
                        return (
                            current_price, 
                            lock_data['predicted_price'], 
                            lock_data['price_change'], 
                            lock_data['sentiment_score'], 
                            lock_data['advice'], 
                            lock_data['risk'] + " (Locked)", 
                            lock_data['headlines'], 
                            lock_data['tp'], 
                            lock_data['sl'], 
                            lock_data['invalid_point'], 
                            current_rsi
                        )
                    else:
                        print(f"🔓 Lock Broken for {coin_id}: Price hit TP/SL.")
                else:
                    print(f"⌛ Lock Expired for {coin_id}. Generating new signal...")
        except Exception as e:
            print(f"Lock File Error: {e}")


    
    #
    data_vals = df['Price'].values.reshape(-1, 1)
    scaled_data = SCALER.transform(data_vals)
    last_60_days = scaled_data[-look_back:] 
    X_test = np.reshape(np.array([last_60_days]), (1, look_back, 1))
    
    pred_scaled = LSTM_MODEL.predict(X_test, verbose=0)[0][0]
    predicted_price = SCALER.inverse_transform([[pred_scaled]])[0][0]
    price_change = ((predicted_price - current_price) / current_price) * 100

    sentiment_score, headlines = fetch_news_sentiment(NEWS_API_KEY, NEWS_QUERY)


    advice, risk = "HOLD", "MEDIUM"
    
    if price_change > 0.8 and current_price > current_ema and current_rsi < 60:
        advice, risk = "STRONG BUY", "LOW (Trend Confirmed)"
    elif price_change > 0.5 and current_price < current_ema:
        advice, risk = "WAIT / TREND WEAK", "MEDIUM (Below EMA)"
    elif current_price < current_ema and (price_change < -0.5 or current_rsi > 70):
        advice, risk = "SELL / EXIT", "HIGH (Bearish)"
    else:
        advice = "NEUTRAL"
        risk = "LOW"


    tp_price = current_price * 1.03  
    sl_price = current_price * 0.985 
    invalid_point = f"Exit below ${sl_price:,.2f}"


    new_lock_data = {
        "coin_id": coin_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_price": current_price,
        "predicted_price": float(predicted_price),
        "price_change": float(price_change),
        "sentiment_score": float(sentiment_score),
        "advice": advice,
        "risk": risk,
        "headlines": headlines,
        "tp": float(tp_price),
        "sl": float(sl_price),
        "invalid_point": invalid_point
    }
    
    with open(LOCK_FILE, 'w') as f:
        json.dump(new_lock_data, f)

    return current_price, predicted_price, price_change, sentiment_score, advice, risk, headlines, tp_price, sl_price, invalid_point, current_rsi


def run_backtest(coin_id, initial_balance=1000):
    try:
        # 1. Load data
        df = pd.read_csv(f'data/{coin_id}_historical_prices.csv', index_col='timestamp', parse_dates=True)

        # 2. Indicators Calculation
        df['RSI'] = calculate_rsi(df['Price'])
        df['EMA7'] = df['Price'].ewm(span=7, adjust=False).mean()
        df['EMA21'] = df['Price'].ewm(span=21, adjust=False).mean()

        balance = initial_balance
        position = 0
        entry_price = 0
        highest_price = 0
        trade_log = []

        prices = df['Price'].values
        rsi_values = df['RSI'].values
        ema7_values = df['EMA7'].values
        ema21_values = df['EMA21'].values

        for i in range(21, len(df)):
            price = prices[i]
            rsi = rsi_values[i]
            ema_fast = ema7_values[i]
            ema_slow = ema21_values[i]

            
            if position == 0:
              
                if coin_id in ["solana", "dogecoin", "shiba-inu"]:
                    if rsi < 62 and ema_fast > ema_slow and price > ema_fast and balance > 0:
                        position = balance / price
                        entry_price = price
                        highest_price = price
                        balance = 0
                        trade_log.append({'Type': 'BUY', 'Price': f"${price:,.6f}", 'Balance': "Active"})

              
                elif coin_id in ["bitcoin", "binancecoin", "avalanche-2"]:
                    trend_strength = ema_fast - ema_slow
                    scale = min(max(trend_strength / ema_slow, 0.7), 1.0) 
                    if ema_fast > ema_slow and price > ema_fast and balance > 0:
                        position = balance * scale / price
                        entry_price = price
                        highest_price = price
                        balance -= position * price
                        trade_log.append({'Type': 'BUY', 'Price': f"${price:,.2f}", 'Balance': f"${balance:,.2f}"})

                else: 
                    if ema_fast > ema_slow and price > (ema_fast * 1.003) and balance > 0:
                        position = balance / price
                        entry_price = price
                        highest_price = price
                        balance = 0
                        trade_log.append({'Type': 'BUY', 'Price': f"${price:,.4f}", 'Balance': "Active"})

         
                highest_price = max(highest_price, price)
                profit_pct = (price - entry_price) / entry_price

              
                if coin_id in ["solana", "dogecoin", "shiba-inu"]:
                    trail_stop = highest_price * 0.95 
                    if rsi > 82 or profit_pct > 0.35 or price < ema_slow or price < trail_stop:
                        balance = position * price
                        position = 0
                        trade_log.append({'Type': 'SELL', 'Price': f"${price:,.6f}", 'Balance': f"${balance:,.2f}"})

                
                elif coin_id in ["bitcoin", "binancecoin", "avalanche-2"]:
                    trend_strength = ema_fast - ema_slow
                    trail_multiplier = 0.92 if trend_strength > 0.03 else 0.96
                    profit_target = 0.28 if trend_strength > 0.03 else 0.22
                    trail_stop = highest_price * trail_multiplier

                    if rsi > 78 or profit_pct > profit_target or price < ema_slow or price < trail_stop:
                        balance += position * price
                        position = 0
                        trade_log.append({'Type': 'SELL', 'Price': f"${price:,.2f}", 'Balance': f"${balance:,.2f}"})

            
                else: 
                    if rsi > 75 or profit_pct > 0.15 or price < ema_slow:
                        balance = position * price
                        position = 0
                        trade_log.append({'Type': 'SELL', 'Price': f"${price:,.4f}", 'Balance': f"${balance:,.2f}"})

        final_val = balance if position == 0 else balance + position * prices[-1]
        return final_val, trade_log

    except Exception as e:
        print("Error in Backtest:", e)
        return initial_balance, []


