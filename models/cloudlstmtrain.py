import os
import argparse
import joblib
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, RepeatVector, TimeDistributed, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

# --- Setup Logging ---
# Configure logger to print to standard console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Feature columns to use for training ---
FEATURE_COLS = ['Current', 'Pressure', 'Temperature', 'Thermocouple', 'Voltage']

def load_and_preprocess_data(file_path):
    """
    Loads CSV data, extracts specified features, and normalizes them.
    Returns the scaled data as a numpy array and the fitted scaler object.
    """
    logging.info(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path, sep=';')
    except FileNotFoundError:
        logging.error(f"Data file not found at {file_path}")
        raise

    # Filter required columns and handle potential missing ones
    df = df[FEATURE_COLS]
    logging.info(f"Initial data shape: {df.shape}")
    
    # Handle missing values by forward then backward fill (updated syntax)
    df.ffill(inplace=True)
    df.bfill(inplace=True)
    
    # MinMax scale features to [0,1]
    scaler = MinMaxScaler()
    normalized_data = scaler.fit_transform(df.values)
    
    logging.info("Data loading and preprocessing complete.")
    return normalized_data, scaler

def create_sequences(data, seq_length):
    """
    Convert 2D array data into overlapping sequences.
    """
    logging.info(f"Creating sequences with length {seq_length}...")
    sequences = []
    for i in range(len(data) - seq_length + 1):
        seq = data[i:i + seq_length]
        sequences.append(seq)
    
    if not sequences:
        raise ValueError("Could not create any sequences. Check data length and sequence length.")
        
    return np.array(sequences)

def build_lstm_autoencoder(seq_length, num_features, encoding_dim=64):
    """
    Build and compile an LSTM Autoencoder model.
    """
    logging.info("Building LSTM autoencoder model...")
    inputs = Input(shape=(seq_length, num_features))
    
    # Encoder
    encoded = LSTM(128, activation='relu', return_sequences=True)(inputs)
    encoded = LSTM(encoding_dim, activation='relu')(encoded)
    
    # Decoder
    decoded = RepeatVector(seq_length)(encoded)
    decoded = LSTM(encoding_dim, activation='relu', return_sequences=True)(decoded)
    decoded = LSTM(128, activation='relu', return_sequences=True)(decoded)
    
    # Output layer
    output = TimeDistributed(Dense(num_features, activation='sigmoid'))(decoded)
    
    model = Model(inputs, output)
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
    
    model.summary(print_fn=logging.info)
    return model

def main(args):
    """
    Main training pipeline.
    """
    # 1. Load and process data
    data, scaler = load_and_preprocess_data(args.data_file)
    
    # 2. Create sequences
    sequences = create_sequences(data, args.seq_length)
    logging.info(f"Final sequences shape: {sequences.shape}")
    
    # 3. Build model
    num_features = sequences.shape[2]
    model = build_lstm_autoencoder(args.seq_length, num_features)
    
    # 4. Train model
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    logging.info("Starting model training...")
    history = model.fit(
        sequences, sequences,
        epochs=args.epochs,
        batch_size=args.batch_size,
        shuffle=True,
        validation_split=0.1, # Use a portion of data for validation
        callbacks=[early_stop]
    )
    logging.info("Training finished.")
    
    # 5. Save model and scaler
    os.makedirs(args.model_dir, exist_ok=True)
    model_path = os.path.join(args.model_dir, "lstm_autoencoder.h5")
    scaler_path = os.path.join(args.model_dir, "scaler.joblib")
    
    model.save(model_path)
    logging.info(f"Model saved to {model_path}")
    
    joblib.dump(scaler, scaler_path)
    logging.info(f"Scaler saved to {scaler_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LSTM Autoencoder Training Script")
    
    # Arguments for file paths
    parser.add_argument('--data-file', type=str, default="data/anomaly-free.csv",
                        help='Path to the input training data CSV file.')
    parser.add_argument('--model-dir', type=str, default="models/saved_models/",
                        help='Directory to save the trained model and scaler.')
                        
    # Arguments for model hyperparameters
    parser.add_argument('--seq-length', type=int, default=30,
                        help='Length of the input sequences for the LSTM.')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of training epochs.')
    parser.add_argument('--batch-size', type=int, default=32,
                        help='Batch size for training.')
                        
    args = parser.parse_args()
    main(args)

