import os
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

DATA_FILE = "data/anomaly-free.csv"
MODEL_SAVE_PATH = "models/saved_models/isolation_forest_model.pkl"

# Corrected feature columns based on your file's header
EXCLUDE_COLS = ['datetime', 'anomaly', 'changepoint']
FEATURE_COLS = ['Current', 'Pressure', 'Temperature', 'Thermocouple', 'Voltage']


def load_data(file_path):
    """Loads a CSV file into a pandas DataFrame using a semicolon as the delimiter."""
    print(f"Loading data from {file_path}")
    df = pd.read_csv(file_path, sep=';')
    return df

def preprocess(df):
    """Selects numeric features and handles missing values."""
    # Ensure all required feature columns exist in the DataFrame
    missing_cols = [col for col in FEATURE_COLS if col not in df.columns]
    if missing_cols:
        print(f"Error: The following feature columns are missing from the CSV file: {missing_cols}")
        raise ValueError("Required feature columns are not found in the data.")
    
    data = df[FEATURE_COLS]
    
    # Correctly handle missing values using ffill and bfill
    data = data.ffill().bfill()
    
    return data

def train_isolation_forest(data):
    """Trains the Isolation Forest model on the provided data."""
    print(f"Training data shape: {data.shape}")
    print("Training Isolation Forest model...")
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,  # Adjust if you expect different anomaly ratio
        max_samples='auto',
        random_state=42,
        verbose=1
    )
    model.fit(data)
    return model

def save_model(model, path):
    """Saves the trained model to a specified file path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved to: {path}")

def main():
    """Main function to run the training pipeline."""
    df = load_data(DATA_FILE)
    data = preprocess(df)
    model = train_isolation_forest(data)
    save_model(model, MODEL_SAVE_PATH)

if __name__ == "__main__":
    main()