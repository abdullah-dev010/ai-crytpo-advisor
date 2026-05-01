import pandas as pd
import requests
import time
import os  
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
DAYS = 365 
CURRENCY = "usd"
UPDATE_INTERVAL_MINUTES = 60  

def fetch_historical_data(coin_id, days, currency):
    """Fetches historical price data with basic error handling."""
    print(f"🌍 Fetching fresh data for {coin_id} from API...")
    URL = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {'vs_currency': currency, 'days': days, 'interval': 'daily'}
    
    try:
        response = requests.get(URL, params=params, timeout=15)
        
       
        if response.status_code == 429:
            print(f"⚠️ Rate limit hit! Waiting 30 seconds to bypass block...")
            time.sleep(30) # 30 second ka break
            response = requests.get(URL, params=params, timeout=15) # Dubara koshish
            
        response.raise_for_status()
        data = response.json()
        
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
        prices.set_index('timestamp', inplace=True)
        prices = prices.rename(columns={'price': 'Price'})
        return prices

    except Exception as e:
        print(f"❌ Error fetching {coin_id}: {e}")
        return None

if __name__ == "__main__":
    print("--- Starting Smart Data Collection ---")
    
    if not os.path.exists('data'):
        os.makedirs('data')

    for name, coin_id in SUPPORTED_ASSETS.items():
        file_path = f'data/{coin_id}_historical_prices.csv'
        
     
        should_fetch = True
        
        
        if os.path.exists(file_path):
      
            file_mod_time = os.path.getmtime(file_path)
            current_time = time.time()
            
         
            if (current_time - file_mod_time) < (UPDATE_INTERVAL_MINUTES * 60):
                print(f"✅ Data for {name} is fresh (Updated < {UPDATE_INTERVAL_MINUTES} mins ago). Skipping API call.")
                should_fetch = False
        
       
        if should_fetch:
            df_prices = fetch_historical_data(coin_id, DAYS, CURRENCY)
            
            if df_prices is not None:
                df_prices.to_csv(file_path)
                print(f"💾 New Data saved: {file_path}")
                
              
                print(f"❄️ Cooling down for 10 seconds...")
                time.sleep(10) 
            else:
                print(f"❌ Failed for {name}. Server might be busy.")
        else:
          
            pass

    print("--- Data Collection Finished ---")