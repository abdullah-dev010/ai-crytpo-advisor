import tensorflow as tf

try:
    m = tf.keras.models.load_model(
        "models/lstm_model_bitcoin.h5",
        compile=False
    )
    print("MODEL OK")
except Exception as e:
    print("ERROR:", e)