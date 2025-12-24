"""
Logic:
1.Writer Thread: I created a thread that generates random data (like amount pattern, frequency, and risk) and writes it to new_data.csv at regular intervals.
2.Read & Analyze Thread: This thread loads the historical data from historical.csv, trains a RandomForest model, and uses it to predict fraud labels for the new data in new_data.csv. It then updates the file with the predicted labels.
3.Plotting Thread: I set up another thread that reads the new_data.csv, separates the fraud and non-fraud data, and adds them to a queue to be plotted.
4.Main Thread: The main thread continuously fetches the data from the queue and updates the plot, showing a comparison between fraud and non-fraud data, refreshing the plot at regular intervals.
"""

import os
import sys
import time
import random
import threading
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from queue import Queue

#global variables
HISTORICAL_FILE = "historical.csv"
NEW_DATA_FILE = "new_data.csv"
WRITE_INTERVAL = 2      # seconds between writes
PLOT_INTERVAL = 10      # seconds between plot updates
stop_event = threading.Event()

# Queue for data to be plotted in the main thread
plot_data_queue = Queue()

# ensuring the file exists
def ensure_file(path: str):
    if not os.path.exists(path):
        # Create empty CSV with headers if file does not exist
        df = pd.DataFrame(columns=['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score', 'label'])
        df.to_csv(path, index=False)

#Thread 1: Writer thread
def writer_thread(filename: str, interval: int):
    print("[writer] started")
    ensure_file(filename)
    try:
        while not stop_event.is_set():
            # Simulating data generation
            amount_pattern = round(random.uniform(20.0, 100.0), 2)
            frequency = round(random.uniform(1.0, 10.0), 2)
            merchant_risk = random.randint(1, 5)
            time_of_day_score = round(random.uniform(0.0, 1.0), 2)
            # No label initially, we will predict it later
            line = f"{amount_pattern},{frequency},{merchant_risk},{time_of_day_score},\n"
            
            # Write new data to the CSV file
            with open(filename, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
            
            print(f"[writer] wrote: {line.strip()}")
            stop_event.wait(interval)
    finally:
        print("[writer] stopped")

# Thread 2: Read and Analysis
def train_model():
    # Load the historical data
    df = pd.read_csv(HISTORICAL_FILE)
    if df.empty:
        return None
    
    # Prepare training data
    X = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
    y = df['label'].fillna(0)  # Fill missing labels with 0 (not fraud)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predictor_thread(filename: str, interval: int):
    print("[predictor] started")
    ensure_file(filename)
    
    try:
        while not stop_event.is_set():
            # Load the new data (without labels) from new_data.csv
            df = pd.read_csv(filename)
            if df.empty:
                stop_event.wait(interval)
                continue
            # Train model on historical data
            model = train_model()
            if model is None:
                stop_event.wait(interval)
                continue
            # Predict labels for the new data
            X_new = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
            predicted_labels = model.predict(X_new)
            # Add the predicted labels to the new data
            df['label'] = predicted_labels
            # Save the data back to the new CSV
            df.to_csv(filename, index=False)
            print(f"[predictor] predicted labels and updated {filename}")
            stop_event.wait(interval)
    
    finally:
        print("[predictor] stopped")

#Thread 3: Plotting fraud and not fraud
def plot_data():
    print("[plotter] started")
    
    try:
        while not stop_event.is_set():
            df = pd.read_csv(NEW_DATA_FILE)
            
            if df.empty or 'label' not in df.columns:
                stop_event.wait(PLOT_INTERVAL)
                continue
            # Separate fraud and non-fraud data
            fraud_data = df[df['label'] == 1]
            not_fraud_data = df[df['label'] == 0]
            # Put data in the queue for plotting
            plot_data_queue.put((fraud_data, not_fraud_data))
            
            stop_event.wait(PLOT_INTERVAL)
    
    finally:
        print("[plotter] stopped")
        
def plot_from_queue():
    print("[plotter - main] started")

    while True:
        if not plot_data_queue.empty():
            fraud_data, not_fraud_data = plot_data_queue.get()

            # Plot for fraud
            plt.figure(figsize=(12, 6))
            plt.subplot(1, 2, 1)
            plt.scatter(fraud_data['amount_pattern'], fraud_data['frequency'], color='red')
            plt.title('Fraud Data')
            plt.xlabel('Amount Pattern')
            plt.ylabel('Frequency')

            # Plot for not fraud
            plt.subplot(1, 2, 2)
            plt.scatter(not_fraud_data['amount_pattern'], not_fraud_data['frequency'], color='blue')
            plt.title('Not Fraud Data')
            plt.xlabel('Amount Pattern')
            plt.ylabel('Frequency')

            plt.tight_layout()
            plt.show()

            # Pause for a while before next update
            time.sleep(PLOT_INTERVAL)

#  Main 
def main():
    # Ensure the historical and new data files exist
    ensure_file(HISTORICAL_FILE)
    ensure_file(NEW_DATA_FILE)

    # Start the threads
    t_writer = threading.Thread(target=writer_thread, args=(NEW_DATA_FILE, WRITE_INTERVAL), daemon=True)
    t_predictor = threading.Thread(target=predictor_thread, args=(NEW_DATA_FILE, 5), daemon=True)
    t_plotter = threading.Thread(target=plot_data, daemon=True)
    
    t_writer.start()
    t_predictor.start()
    t_plotter.start()

    # Main thread responsible for plotting
    plot_from_queue()

    print("\nRunning. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        t_writer.join(timeout=2)
        t_predictor.join(timeout=2)
        t_plotter.join(timeout=2)
        print("Done.")

if __name__ == "__main__":
    main()

