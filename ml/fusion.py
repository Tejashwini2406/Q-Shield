import os
import numpy as np
from ml.edge.edge_if import EdgeIsolationForest
from ml.cloud_lstm.cloud_lstm import CloudLSTMDetector

print("[DEBUG] fusion.py loaded")

# Thresholds for severity
EDGE_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.8,
}

CLOUD_THRESHOLDS = {
    "low": 0.4,
    "medium": 0.7,
    "high": 0.9,
}

def get_severity(edge_score, cloud_score):
    if edge_score > EDGE_THRESHOLDS["high"] or cloud_score > CLOUD_THRESHOLDS["high"]:
        return "high"
    elif edge_score > EDGE_THRESHOLDS["medium"] or cloud_score > CLOUD_THRESHOLDS["medium"]:
        return "medium"
    elif edge_score > EDGE_THRESHOLDS["low"] or cloud_score > CLOUD_THRESHOLDS["low"]:
        return "low"
    else:
        return "normal"

def run_fusion():
    print("[FUSION] Running test...")

    # Load models
    edge_model = EdgeIsolationForest()
    cloud_model = CloudLSTMDetector()

    # ✅ Edge expects list of dicts
    test_data_edge = [{"voltage": 220, "current": 10} for _ in range(10)]

    # ✅ Cloud expects numpy array
    test_data_cloud = np.array([[220, 10]] * 10)

    # Run anomaly scoring
    edge_score = edge_model.score(test_data_edge)
    cloud_score = cloud_model.score(test_data_cloud)

    severity = get_severity(edge_score, cloud_score)

    result = {
        "edge_score": edge_score,
        "cloud_score": cloud_score,
        "severity": severity,
    }

    print(f"[FUSION] Result: {result}")
    return result

if __name__ == "__main__":
    run_fusion()
