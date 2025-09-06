import os
import joblib
import pandas as pd
import logging
import numpy as np
from typing import Dict, List

# Suppress TensorFlow logs for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

# --- Configuration ---
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
MODEL_PATH = "models/saved_models/lstm_autoencoder.h5"
SCALER_PATH = "models/saved_models/scaler.joblib"
FEATURE_COLS = ['Current', 'Pressure', 'Temperature', 'Thermocouple', 'Voltage']
SEQUENCE_LENGTH = 30
RECONSTRUCTION_THRESHOLD = 0.01

# --- Global variables for model and scaler ---
lstm_model = None
scaler = None

def load_model_and_scaler():
    """Loads the Keras model and the scaler into global variables."""
    global lstm_model, scaler
    try:
        if os.path.exists(MODEL_PATH):
            lstm_model = load_model(MODEL_PATH, compile=False)
            logging.info(f"Successfully loaded Keras model from {MODEL_PATH}.")
        else:
            logging.error(f"Keras model not found at {MODEL_PATH}.")
            
        if os.path.exists(SCALER_PATH):
            scaler = joblib.load(SCALER_PATH)
            logging.info(f"Successfully loaded Scaler from {SCALER_PATH}.")
        else:
            logging.error(f"Scaler not found at {SCALER_PATH}.")
            
    except Exception as e:
        logging.error(f"An error occurred during model loading: {e}")
        lstm_model = None
        scaler = None

def classify_severity(score: float) -> str:
    """Classifies the normalized anomaly score into a severity category."""
    if score < 0.25:
        return "low"
    elif score < 0.6:
        return "medium"
    else:
        return "high"

def get_anomaly_score(telemetry_sequence: List[Dict]) -> Dict:
    """
    Performs inference on a sequence of telemetry data using the LSTM Autoencoder.
    """
    global lstm_model, scaler

    if lstm_model is None or scaler is None:
        load_model_and_scaler()
        if lstm_model is None or scaler is None:
            return {'score': 0.0, 'severity': 'unloaded'}

    if len(telemetry_sequence) < SEQUENCE_LENGTH:
        logging.error(f"Input length {len(telemetry_sequence)} is less than required {SEQUENCE_LENGTH}.")
        return {'score': 0.0, 'severity': 'error'}

    try:
        # Prepare the data from the sequence
        df = pd.DataFrame(telemetry_sequence[-SEQUENCE_LENGTH:])[FEATURE_COLS]
        data_scaled = scaler.transform(df.values)
        sequence = np.expand_dims(data_scaled, axis=0)
    except Exception as e:
        logging.error(f"Error preparing data for LSTM inference: {e}")
        return {'score': 0.0, 'severity': 'error'}

    # Get the reconstruction and calculate the mean squared error
    reconstructed = lstm_model.predict(sequence, verbose=0)
    mse = np.mean(np.power(sequence - reconstructed, 2))
    
    # Normalize the score based on the pre-defined threshold
    anomaly_score = min(1.0, mse / RECONSTRUCTION_THRESHOLD)

    return {
        'score': float(anomaly_score),
        'severity': classify_severity(anomaly_score)
    }

if __name__ == "__main__":
    load_model_and_scaler()

    if lstm_model and scaler:
        logging.info("--- Testing Cloud LSTM Anomaly Detection ---")
        
        normal_data = {'Current': 1.82, 'Pressure': 0.1, 'Temperature': 89.6, 'Thermocouple': 27.0, 'Voltage': 230.0}
        anomaly_data = {'Current': 10.0, 'Pressure': -10.0, 'Temperature': 100.0, 'Thermocouple': 5.0, 'Voltage': 300.0}
        
        # Create test sequences
        normal_sequence = [normal_data] * SEQUENCE_LENGTH
        anomaly_sequence = [normal_data] * (SEQUENCE_LENGTH - 1) + [anomaly_data]

        print(f"[CloudLSTM] Normal sequence test: {get_anomaly_score(normal_sequence)}")
        print(f"[CloudLSTM] Anomalous sequence test: {get_anomaly_score(anomaly_sequence)}")


