import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "edge_if.pkl")

class EdgeIsolationForest:
    """Wraps an Isolation Forest model for edge device anomaly detection."""

    def __init__(self, contamination=0.01, random_state=42):
        self.model = None
        self.contamination = contamination
        self.random_state = random_state
        self.min_score = 0
        self.max_score = 1

    def train(self, X):
        """Trains the model and calibrates normalization bounds."""
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state
        )
        self.model.fit(X)

        # Calibrate normalization bounds. Lower scores are more anomalous in decision_function.
        scores = self.model.decision_function(X)
        self.min_score = np.percentile(scores, 1)
        self.max_score = np.max(scores)

        save_package = {
            'model': self.model,
            'min_score': self.min_score,
            'max_score': self.max_score
        }
        joblib.dump(save_package, MODEL_PATH)
        print(f"[EDGE IF] Model trained and saved to {MODEL_PATH}")

    def load(self):
        """Loads model and calibration parameters from disk."""
        try:
            save_package = joblib.load(MODEL_PATH)
            self.model = save_package['model']
            self.min_score = save_package['min_score']
            self.max_score = save_package['max_score']
            print(f"[EDGE IF] Model loaded from {MODEL_PATH}")
            return True
        except FileNotFoundError:
            print("[EDGE IF] Model not found, please train it first.")
            return False

    def score(self, data):
        """Calculates a normalized anomaly score between 0.0 (normal) and 1.0 (anomalous)."""
        if self.model is None:
            if not self.load():
                raise Exception("Model file not found. Train the model before scoring.")

        if isinstance(data, dict):
            data = [data]

        arr = np.array([[d["Voltage"], d["Current"]] for d in data])
        raw_scores = self.model.decision_function(arr)
        normalized_scores = (raw_scores - self.min_score) / (self.max_score - self.min_score)
        
        # Invert score: final score = 1.0 - normalized_score to map anomalies to 1.0.
        final_scores = 1.0 - normalized_scores
        return float(np.clip(final_scores, 0, 1).mean())


def load_csv(file_path):
    """Loads a CSV and auto-detects separator (comma or semicolon)."""
    try:
        df = pd.read_csv(file_path, sep=";")
        if len(df.columns) <= 1:
            df = pd.read_csv(file_path, sep=",")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        raise
    return df


if __name__ == "__main__":
    # --- Configuration ---
    # Use a single file that contains both normal and anomalous data.
    DATA_FILE_PATH = "ml/data/1.csv"
    FEATURE_COLUMNS = ['Voltage', 'Current']
    LABEL_COLUMN = 'anomaly'

    # --- Data Loading ---
    print(f"Loading data from: {DATA_FILE_PATH}")
    try:
        data_df = load_csv(DATA_FILE_PATH)
    except FileNotFoundError:
        print(f"FATAL: Data file not found at {DATA_FILE_PATH}")
        exit()

    # Verify columns before proceeding
    if not all(col in data_df.columns for col in FEATURE_COLUMNS):
        print(f"Missing required columns in data file. Needed: {FEATURE_COLUMNS}")
        print(f"Found: {data_df.columns.tolist()}")
        exit()
    
    if LABEL_COLUMN not in data_df.columns:
        print(f"FATAL: Label column '{LABEL_COLUMN}' not found in file.")
        exit()

    # --- Data Preparation ---
    normal_df = data_df[data_df[LABEL_COLUMN] == 0]
    anomaly_df = data_df[data_df[LABEL_COLUMN] == 1]
    
    # Train the model using only the normal samples from this file.
    training_data_array = normal_df[FEATURE_COLUMNS].values
    print(f"Loaded {len(training_data_array)} normal samples for training.")

    # --- Training Phase ---
    print("--- Model Training Phase ---")
    detector = EdgeIsolationForest()
    detector.train(training_data_array)

    # --- Scoring Test Phase ---
    print("\n--- Model Scoring Test Phase ---")
    
    # Test 1: Score a normal sample from the same file
    if not normal_df.empty:
        sample_to_test = normal_df.iloc[0].to_dict()
        score_normal = detector.score(sample_to_test)
        print(f"Score for a real NORMAL sample: {score_normal:.4f}")
    else:
        print("No normal samples found in test file for comparison.")

    # Test 2: Score an anomaly sample from the same file
    if not anomaly_df.empty:
        sample_to_test = anomaly_df.iloc[0].to_dict()
        score_anomaly = detector.score(sample_to_test)
        print(f"Score for a real ANOMALY sample: {score_anomaly:.4f}")
    else:
        print("No anomaly samples found in test file for testing.")