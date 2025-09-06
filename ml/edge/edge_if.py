import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

# Path where the trained model will be saved (inside same folder as this file)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "edge_if.pkl")

def generate_normal_samples(n=1000):
    """
    Generate synthetic telemetry data that looks "normal".
    - voltage around 220 ± 5
    - current around 10 ± 2
    Used to train the anomaly detection model.
    """
    voltages = 220 + np.random.randint(-5, 6, size=n)
    currents = 10 + np.random.randint(-2, 3, size=n)
    return np.column_stack((voltages, currents))  # shape (n, 2)

class EdgeIsolationForest:
    """
    Wrapper around an Isolation Forest model for detecting anomalies
    in simple telemetry (voltage, current).
    """

    def __init__(self, contamination=0.01, random_state=42):
        """
        contamination: expected proportion of anomalies in training data
        random_state: ensures reproducibility
        """
        self.model = None
        self.contamination = contamination
        self.random_state = random_state

    def train(self, X=None):
        """
        Train the Isolation Forest on provided data X.
        If X is None, generate synthetic 'normal' samples for training.
        Save the trained model to disk.
        """
        if X is None:
            X = generate_normal_samples()
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state
        )
        self.model.fit(X)
        joblib.dump(self.model, MODEL_PATH)  # serialize model
        print(f"[EDGE IF] Model trained and saved to {MODEL_PATH}")

    def load(self):
        """
        Load a trained model from disk.
        If not found, fall back to training a new one.
        """
        try:
            self.model = joblib.load(MODEL_PATH)
            print(f"[EDGE IF] Model loaded from {MODEL_PATH}")
        except FileNotFoundError:
            print("[EDGE IF] Model not found, training new one...")
            self.train()

    def score(self, data):
        """
        Score the input data for anomalies.
        data: can be a single dict or a list of dicts with keys 'voltage' and 'current'.
        Returns a float score between 0.0 (normal) and 1.0 (anomalous).
        """
        if self.model is None:
            self.load()

        if isinstance(data, dict):
            data = [data]  # wrap single dict into a list

        arr = np.array([[d["voltage"], d["current"]] for d in data])
        preds = self.model.predict(arr)  # 1 = normal, -1 = anomaly
        # map: normal=0.0, anomaly=1.0
        scores = [1.0 if p == -1 else 0.0 for p in preds]
        return float(np.mean(scores))


# Quick self-test when running this file directly
if __name__ == "__main__":
    detector = EdgeIsolationForest()
    detector.load()  # either load from disk or train a new model
    test_sample = {"voltage": 230, "current": 12}  # slightly abnormal values
    score = detector.score(test_sample)
    print(f"[EDGE IF] Test sample anomaly score: {score}")
