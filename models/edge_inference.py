import os
import joblib
import pandas as pd
import logging
import sys # Import sys for system operations
from contextlib import redirect_stdout, redirect_stderr # Import redirection tools

# Set joblib verbosity to 0 via environment variable (keeping as a best practice)
os.environ['JOBLIB_VERBOSITY'] = '0'

# Suppress standard logging messages
logging.getLogger('joblib').setLevel(logging.WARNING)

MODEL_SAVE_PATH = "models/saved_models/isolation_forest_model.pkl"
FEATURE_COLS = ['Current', 'Pressure', 'Temperature', 'Thermocouple', 'Voltage']
isolation_forest_model = None

def load_model():
    global isolation_forest_model
    try:
        if os.path.exists(MODEL_SAVE_PATH):
            isolation_forest_model = joblib.load(MODEL_SAVE_PATH)
            print("Successfully loaded the Isolation Forest model.")
        else:
            print(f"Error: Model not found at {MODEL_SAVE_PATH}. Please train it first.")
            isolation_forest_model = None
    except Exception as e:
        print(f"Error loading model: {e}")
        isolation_forest_model = None

def normalize_score(score):
    min_score = -0.1
    max_score = 0.0
    normalized = (score - min_score) / (max_score - min_score)
    anomaly_score = 1 - normalized
    anomaly_score = max(0.0, min(1.0, anomaly_score))
    return float(anomaly_score)

def classify_severity(score):
    if score < 0.15:
        return "low"
    elif score < 0.4:
        return "medium"
    else:
        return "high"

def get_anomaly_scores(telemetry_data):
    global isolation_forest_model

    if isolation_forest_model is None:
        load_model()
        if isolation_forest_model is None:
            return {'score': 0.0, 'severity': 'unknown'}

    if not all(k in telemetry_data for k in FEATURE_COLS):
        print("Error: Missing required feature columns.")
        return {'score': 0.0, 'severity': 'unknown'}

    try:
        data_df = pd.DataFrame([telemetry_data])[FEATURE_COLS]
    except Exception as e:
        print(f"Error converting data to DataFrame: {e}")
        return {'score': 0.0, 'severity': 'unknown'}

    # --- Start Redirection ---
    # Temporarily redirect stdout and stderr to os.devnull (a system black hole)
    # to capture and discard print statements from the underlying library.
    with open(os.devnull, 'w') as devnull:
        with redirect_stdout(devnull), redirect_stderr(devnull):
            raw_score = isolation_forest_model.decision_function(data_df)[0]
    # --- End Redirection ---

    normalized = normalize_score(raw_score)
    severity = classify_severity(normalized)
    return {'score': normalized, 'severity': severity}

if __name__ == "__main__":
    load_model()

    if isolation_forest_model:
        normal_data = {
            'Current': 1.82,
            'Pressure': 0.1,
            'Temperature': 89.6,
            'Thermocouple': 27.0,
            'Voltage': 230.0
        }
        print("[Edge IF] Normal data test:", get_anomaly_scores(normal_data))

        anomaly_data = {
            'Current': 10.0,
            'Pressure': -10.0,
            'Temperature': 100.0,
            'Thermocouple': 5.0,
            'Voltage': 300.0
        }
        print("[Edge IF] Anomalous data test:", get_anomaly_scores(anomaly_data))