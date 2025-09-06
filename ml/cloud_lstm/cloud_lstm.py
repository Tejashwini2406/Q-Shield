import numpy as np
import tensorflow as tf
from tensorflow import Sequential
from tensorflow import LSTM, Dense
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "cloud_lstm.h5")

def generate_synthetic_sequence(n_samples=500, seq_len=10):
    """
    Generate synthetic normal telemetry sequences:
    - voltage ~ 220 ± small noise
    - current ~ 10 ± small noise
    """
    X, y = [], []
    for _ in range(n_samples):
        base_v = 220 + np.random.randint(-3, 4)
        base_c = 10 + np.random.randint(-1, 2)
        seq = []
        for _ in range(seq_len):
            seq.append([
                base_v + np.random.randint(-2, 3),
                base_c + np.random.randint(-1, 2)
            ])
        X.append(seq)
        y.append(0)  # all normal = 0
    return np.array(X), np.array(y)

def build_model(seq_len=10, features=2):
    model = Sequential([
        LSTM(32, input_shape=(seq_len, features)),
        Dense(1, activation="sigmoid")
    ])
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model

def train_cloud_lstm():
    X, y = generate_synthetic_sequence()
    model = build_model()
    model.fit(X, y, epochs=3, batch_size=32, verbose=1)
    model.save(MODEL_PATH)
    print(f"[CLOUD LSTM] Model trained and saved to {MODEL_PATH}")
    return model

def load_cloud_lstm():
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        print(f"[CLOUD LSTM] Model loaded from {MODEL_PATH}")
    except:
        print("[CLOUD LSTM] Model not found, training new one...")
        model = train_cloud_lstm()
    return model

def score_sequence(model, seq):
    """
    seq: numpy array with shape (seq_len, 2)
    returns: anomaly probability between 0.0 and 1.0
    """
    seq = np.expand_dims(seq, axis=0)  # add batch dimension
    prob = model.predict(seq, verbose=0)[0][0]
    return float(prob)

# ------------------------
# Class wrapper for fusion
# ------------------------
class CloudLSTMDetector:
    def __init__(self, seq_len=10, features=2):
        self.seq_len = seq_len
        self.features = features
        self.model = load_cloud_lstm()

    def score(self, seq):
        """
        seq: numpy array with shape (seq_len, 2)
        returns: anomaly probability between 0.0 and 1.0
        """
        return score_sequence(self.model, seq)

if __name__ == "__main__":
    detector = CloudLSTMDetector()
    # test with a normal sequence
    seq = np.array([[220, 10]] * 10)
    score = detector.score(seq)
    print(f"[CLOUD LSTM] Test sequence anomaly score: {score}")
