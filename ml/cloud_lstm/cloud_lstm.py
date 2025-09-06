import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, RepeatVector, TimeDistributed
from sklearn.preprocessing import MinMaxScaler
import joblib # Used for saving/loading the scaler object
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "cloud_lstm_autoencoder.h5")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "cloud_scaler.pkl") # Need to save the scaler
SEQ_LEN = 10
FEATURES = 2

def generate_synthetic_normal_data(n_samples=1000, seq_len=SEQ_LEN):
    """Generate synthetic normal telemetry sequences."""
    X = []
    for _ in range(n_samples):
        base_v = 220 + np.random.uniform(-3, 3)
        base_c = 10 + np.random.uniform(-1, 1)
        seq = []
        for _ in range(seq_len):
            seq.append([
                base_v + np.random.normal(0, 0.5), # Smaller, more realistic noise
                base_c + np.random.normal(0, 0.2)
            ])
        X.append(seq)
    return np.array(X)

# Autoencoder Model
def build_autoencoder(seq_len=SEQ_LEN, features=FEATURES):
    
    inputs = Input(shape=(seq_len, features))

    # compresses the sequence
    encoder = LSTM(32, activation='relu', return_sequences=True)(inputs) 
    encoder = LSTM(16, activation='relu', return_sequences=False)(encoder)
    
    # Repeat the latent vector for each time step
    bridge = RepeatVector(seq_len)(encoder) 
    
    # reconstructs the sequence
    decoder = LSTM(16, activation='relu', return_sequences=True)(bridge) 
    decoder = LSTM(32, activation='relu', return_sequences=True)(decoder)
    
    output = TimeDistributed(Dense(features))(decoder)
    
    model = Model(inputs=inputs, outputs=output)
    model.compile(optimizer="adam", loss="mae")
    return model

# --- 2. Data Preprocessing and Training ---
def train_cloud_lstm(data):
    """Trains the autoencoder on normal data."""

    data_reshaped = data.reshape(-1, FEATURES)
    
    # Scale data: Crucial for LSTM performance. Scale features to [0, 1].
    scaler = MinMaxScaler()
    scaled_data_reshaped = scaler.fit_transform(data_reshaped)
    
    scaled_data = scaled_data_reshaped.reshape(data.shape)
    
    print("[CLOUD LSTM] Training autoencoder...")
    model = build_autoencoder()

    model.fit(scaled_data, scaled_data, epochs=10, batch_size=32, shuffle=True, validation_split=0.1, verbose=1)
    
    # Save both model and scaler
    model.save(MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"[CLOUD LSTM] Model trained and saved to {MODEL_PATH}")
    print(f"[CLOUD LSTM] Scaler saved to {SCALER_PATH}")
    return model, scaler

def load_cloud_lstm():
    """Loads model and scaler, trains if not found."""
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        print(f"[CLOUD LSTM] Model loaded from {MODEL_PATH}")
        print(f"[CLOUD LSTM] Scaler loaded from {SCALER_PATH}")
    except:
        print("[CLOUD LSTM] Model not found, training new one...")
        normal_data = generate_synthetic_normal_data()
        model, scaler = train_cloud_lstm(normal_data) 
    
    return model, scaler

# --- Renamed function for clarity ---
def calculate_raw_error(model, scaler, seq):
    """Calculates anomaly score based on reconstruction error."""
    seq_reshaped = seq.reshape(-1, FEATURES)
    scaled_seq_reshaped = scaler.transform(seq_reshaped)
    scaled_seq = scaled_seq_reshaped.reshape(1, SEQ_LEN, FEATURES) # Model expects 3D input

    # Get reconstructed sequence
    reconstructed_seq = model.predict(scaled_seq, verbose=0)
    
    # Whatever value we get here is the anomaly score (raw reconstruction error)
    error = np.mean(np.abs(scaled_seq - reconstructed_seq)) 
    return float(error)

# ------------------------
# Class wrapper for fusion
# ------------------------
class CloudLSTMDetector:
    def __init__(self):
        self.model, self.scaler = load_cloud_lstm()
        # --- NEW: Calibration step ---
        # Calibrate normalization bounds using a validation set of normal data
        print("[CLOUD LSTM] Calibrating normalization thresholds...")
        validation_data = generate_synthetic_normal_data(n_samples=500)
        self.min_error, self.max_error = self.calibrate_thresholds(validation_data)

    def calibrate_thresholds(self, calibration_data):
        """Calculates reconstruction errors on normal data to find normalization bounds."""
        errors = []
        for seq in calibration_data:
            raw_error = calculate_raw_error(self.model, self.scaler, seq)
            errors.append(raw_error)
        
        min_error = np.min(errors) * 0.9 
        
        # --- ADJUSTMENT HERE ---
        # Increase the percentile to create more headroom for normal data.
        # This pushes normal scores closer to 0.0.
        # max_error = np.percentile(errors, 99.0) # Original value
        max_error = np.percentile(errors, 99.9) # New value for better separation
        
        print(f"[CLOUD LSTM] Calibration complete. Min Error: {min_error:.6f}, Max Error (99.9th percentile): {max_error:.6f}")
        return min_error, max_error

    def score(self, seq_data):
        """Calculates a normalized reconstruction error score between 0.0 and 1.0."""
        # 1. Calculate the raw reconstruction error
        raw_error = calculate_raw_error(self.model, self.scaler, seq_data)
        
        # 2. Normalize the error to a 0-1 scale using calibrated bounds
        normalized_score = (raw_error - self.min_error) / (self.max_error - self.min_error)
        
        # Clip the result to ensure it strictly stays within [0, 1] range,
        # even if a new error exceeds the calibrated maximum error.
        return float(np.clip(normalized_score, 0, 1))

if __name__ == "__main__":
    detector = CloudLSTMDetector()
    
    # --- Test with a normal sequence ---
    normal_seq = np.array([[220 + np.random.rand(), 10 + np.random.rand()] for _ in range(SEQ_LEN)])
    normal_score = detector.score(normal_seq)
    print(f"\n[Test Result] Normal sequence normalized score: {normal_score:.6f}") # Should be close to 0.0

    # --- Test with an anomalous sequence ---
    anomalous_seq = np.array([[220, 10] for _ in range(5)] + [[300, 15] for _ in range(5)]) # Sudden jump
    anomaly_score = detector.score(anomalous_seq)
    print(f"[Test Result] Anomalous sequence normalized score: {anomaly_score:.6f}") # Should be close to 1.0