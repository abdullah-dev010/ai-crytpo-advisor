
import pandas as pd
import numpy as np
import joblib 
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.model_selection import train_test_split
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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

def create_dataset(data, look_back=60):
    """Creates time series data for LSTM training."""
    X, Y = [], []
    for i in range(len(data) - look_back - 1):
        a = data[i:(i + look_back), 0]
        X.append(a)
        Y.append(data[i + look_back, 0])
    return np.array(X), np.array(Y)



def train_lstm_model(df_prices, look_back=60):
    print("\n--- Starting LSTM Model Training ---")
    
   
    data = df_prices['Price'].values.reshape(-1, 1)
    

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    X, Y = create_dataset(scaled_data, look_back)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, shuffle=False)
    
   
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X_train.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False)) 
    model.add(Dropout(0.2))
    model.add(Dense(units=1))
    
    model.compile(optimizer='adam', loss='mean_squared_error')
    

    print("Training model...")
    model.fit(X_train, Y_train, epochs=20, batch_size=32, verbose=1) 
    
   
    model.save('models/lstm_model.h5')
    joblib.dump(scaler, 'models/scaler.pkl') 
    print("LSTM Model and Scaler saved successfully!")
    
    return model, scaler


def get_sentiment_score(text_list):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_scores = [analyzer.polarity_scores(text)['compound'] for text in text_list]
    avg_score = sum(sentiment_scores) / len(sentiment_scores)
    return avg_score




if __name__ == "__main__":
    

    test_texts = [
        "Bitcoin price is soaring high, experts predict massive gains!",
        "Crypto market remains flat today, no major movements."
    ]
    score = get_sentiment_score(test_texts)
    print("\n--- VADER Sentiment Analysis Test ---")
    print(f"Average Compound Score: {score:.4f}")


    print("\n--- Starting LSTM Model Training for Multiple Assets ---")
    

    for name, coin_id in SUPPORTED_ASSETS.items():
        try:
        
            csv_path = f'data/{coin_id}_historical_prices.csv'
            df_prices = pd.read_csv(csv_path, index_col='timestamp', parse_dates=True)
            
            print(f"\n[✅ Training {name} ({coin_id})] Data Points: {len(df_prices)}")
            
            lstm_model, scaler = train_lstm_model(df_prices, LOOK_BACK)
    
            lstm_model.save(f'models/lstm_model_{coin_id}.h5')
            joblib.dump(scaler, f'models/scaler_{coin_id}.pkl')
            
            print(f"[SUCCESS] Trained and saved model for {name}.")

        except FileNotFoundError:
    
            print(f"❌ Error: Data not found for {name} at {csv_path}. Please run data_collection.py first.")
        except Exception as e:
            print(f"❌ Critical Error during training {name}: {e}")