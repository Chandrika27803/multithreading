import os
import sys
import time
import random
import threading
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt

# ---------------- Constants ----------------
FILENAME = "historical.csv"
WRITE_INTERVAL = 2      # seconds between writes
PLOT_INTERVAL = 10      # seconds between plot updates
stop_event = threading.Event()

# ---------------- Utilities ----------------
def ensure_file(path: str):
    if not os.path.exists(path):
        # Create empty CSV with headers
        df = pd.DataFrame(columns=['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score', 'label'])
        df.to_csv(path, index=False)

# ---------------- Thread 1: Writer ----------------
def writer_thread(filename: str, interval: int):
    print("[writer] started")
    ensure_file(filename)
    try:
        while not stop_event.is_set():
            amount_pattern = round(random.uniform(20.0, 100.0), 2)
            frequency = round(random.uniform(1.0, 10.0), 2)
            merchant_risk = random.randint(1, 5)
            time_of_day_score = round(random.uniform(0.0, 1.0), 2)
            line = f"{amount_pattern},{frequency},{merchant_risk},{time_of_day_score},\n"
            
            with open(filename, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
            
            print(f"[writer] wrote: {line.strip()}")
            stop_event.wait(interval)
    finally:
        print("[writer] stopped")

# ---------------- Thread 2: Predictor ----------------
def train_model(filename: str):
    df = pd.read_csv(filename)
    if df.empty:
        return None
    X = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
    y = df['label'].fillna(0)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predictor_thread(filename: str, interval: int):
    print("[predictor] started")
    ensure_file(filename)
    try:
        while not stop_event.is_set():
            df = pd.read_csv(filename)
            if df.empty:
                stop_event.wait(interval)
                continue
            
            # Train model on current data
            model = train_model(filename)
            if model is None:
                stop_event.wait(interval)
                continue
            
            # Predict labels for rows with missing labels
            mask = df['label'].isna() | (df['label'] == '')
            if mask.any():
                X_new = df.loc[mask, ['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
                df.loc[mask, 'label'] = model.predict(X_new)
                df.to_csv(filename, index=False)
                print(f"[predictor] predicted {mask.sum()} rows")
            
            stop_event.wait(interval)
    finally:
        print("[predictor] stopped")

# ---------------- Main Thread: Plotter ----------------
def plot_data(filename: str):
    if not os.path.exists(filename):
        return
    df = pd.read_csv(filename)
    if df.empty or 'label' not in df.columns:
        return
    
    fraud_data = df[df['label'] == 1]
    not_fraud_data = df[df['label'] == 0]
    
    plt.figure(figsize=(10,6))
    if not fraud_data.empty:
        plt.scatter(fraud_data['amount_pattern'], fraud_data['frequency'], color='red', label='Fraud', alpha=0.6)
    if not not_fraud_data.empty:
        plt.scatter(not_fraud_data['amount_pattern'], not_fraud_data['frequency'], color='blue', label='Not Fraud', alpha=0.6)
    plt.xlabel("Amount Pattern")
    plt.ylabel("Frequency")
    plt.title("Fraud vs Not Fraud Data")
    plt.legend()
    plt.show()

# ---------------- Main ----------------
def main():
    ensure_file(FILENAME)
    
    t_writer = threading.Thread(target=writer_thread, args=(FILENAME, WRITE_INTERVAL), daemon=True)
    t_predictor = threading.Thread(target=predictor_thread, args=(FILENAME, WRITE_INTERVAL), daemon=True)
    
    t_writer.start()
    t_predictor.start()
    
    print("Running... Press Ctrl+C to stop.\n")
    try:
        while True:
            # Plot in main thread safely
            plot_data(FILENAME)
            time.sleep(PLOT_INTERVAL)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        t_writer.join(timeout=2)
        t_predictor.join(timeout=2)
        print("Done.")

if __name__ == "__main__":
    main()

