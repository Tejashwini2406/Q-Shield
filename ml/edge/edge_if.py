import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "edge_if.pkl")

def generate_normal_samples(n=1000):
    """Generates synthetic normal telemetry data for training."""
    voltages = 220 + np.random.randint(-5, 6, size=n)
    currents = 10 + np.random.randint(-2, 3, size=n)
    return np.column_stack((voltages, currents)) # shape (n, 2)

class EdgeIsolationForest:
    """Wraps an Isolation Forest model for edge device anomaly detection."""

    def __init__(self, contamination=0.01, random_state=42):
        self.model = None
        self.contamination = contamination
        self.random_state = random_state
        self.min_score = 0
        self.max_score = 1

    def train(self, X=None):
        """Trains the model and calibrates normalization bounds."""
        if X is None:
            X = generate_normal_samples()
            
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state
        )
        self.model.fit(X)

        # Calibrate normalization bounds based on training data scores.
        # In Isolation Forest's decision_function, lower scores are more anomalous.
        scores = self.model.decision_function(X)
        self.min_score = np.percentile(scores, 1)  # Lower bound captures 1st percentile outliers
        self.max_score = np.max(scores)           # Upper bound captures most normal point

        # Save model and calibration parameters together for consistent scoring later.
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
        except FileNotFoundError:
            print("[EDGE IF] Model not found, training new one...")
            self.train()

    def score(self, data):
        """Calculates a normalized anomaly score between 0.0 (normal) and 1.0 (anomalous)."""
        if self.model is None:
            self.load()

        if isinstance(data, dict):
            data = [data]

        arr = np.array([[d["voltage"], d["current"]] for d in data])
        raw_scores = self.model.decision_function(arr)
        
        # Normalize raw scores to a 0-1 range.
        normalized_scores = (raw_scores - self.min_score) / (self.max_score - self.min_score)
        
        # Invert score: final score = 1.0 - normalized_score.
        # This maps low raw scores (anomalies) to high final scores (~1.0),
        # and high raw scores (normal) to low final scores (~0.0).
        final_scores = 1.0 - normalized_scores
        
        return float(np.clip(final_scores, 0, 1).mean())

# Quick self-test when running this file directly
if __name__ == "__main__":
    detector = EdgeIsolationForest()
    detector.load()

    print("\n--- Testing ---")
    normal_sample = {"voltage": 221, "current": 10}
    score_normal = detector.score(normal_sample)
    print(f"[EDGE IF] Normal sample score: {score_normal:.4f}")

    abnormal_sample = {"voltage": 250, "current": 20}
    score_abnormal = detector.score(abnormal_sample)
    print(f"[EDGE IF] Abnormal sample score: {score_abnormal:.4f}")