import os
import time
import random
import threading
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from queue import Queue

# Global variables
NEW_DATA_FILE = "new_data.csv"
WRITE_INTERVAL = 2
PREDICT_INTERVAL = 4
stop_event = threading.Event()
plot_data_queue = Queue()

FILE_COLUMNS = ['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score', 'label']


def ensure_file(path: str):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=FILE_COLUMNS)
        df.to_csv(path, index=False)
    else:
        # Fix corrupted or missing header
        df = pd.read_csv(path)
        missing = [c for c in FILE_COLUMNS if c not in df.columns]
        if missing:
            print(f"[fix] repairing corrupted file: {path}")
            df = pd.DataFrame(columns=FILE_COLUMNS)
            df.to_csv(path, index=False)

# WRITER THREAD
def writer_thread(filename: str, interval: int):
    print("[writer] started")
    ensure_file(filename)

    while not stop_event.is_set():
        amount_pattern = round(random.uniform(20.0, 100.0), 2)
        frequency = round(random.uniform(1.0, 10.0), 2)
        merchant_risk = random.randint(1, 5)
        time_of_day_score = round(random.uniform(0.0, 1.0), 2)

        # Label set to random 0 or 1 (simulating ground truth for training)
        label = random.randint(0, 1)
        line = f"{amount_pattern},{frequency},{merchant_risk},{time_of_day_score},{label}\n"

        with open(filename, "a", encoding="utf-8") as f:
            f.write(line)

        print(f"[writer] wrote: {line.strip()}")
        stop_event.wait(interval)

    print("[writer] stopped")

# TRAIN MODEL
def train_model():
    df = pd.read_csv(NEW_DATA_FILE)

    if df.empty:
        return None
    df = df.dropna()
    X = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
    y = df['label']
    model = RandomForestClassifier(n_estimators=80, random_state=42)
    model.fit(X, y)
    return model

# PREDICTOR THREAD
def predictor_thread(filename: str, interval: int):
    print("[predictor] started")
    ensure_file(filename)
    while not stop_event.is_set():
        df = pd.read_csv(filename)
        if df.empty:
            stop_event.wait(interval)
            continue
        # Clean incomplete/corrupted rows
        df = df.dropna(subset=['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score'])
        model = train_model()
        if model is None:
            stop_event.wait(interval)
            continue
        X_new = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
        predicted = model.predict(X_new)
        df['label'] = predicted
        df.to_csv(filename, index=False)
        print(f"[predictor] updated labels in {filename}")
        stop_event.wait(interval)
    print("[predictor] stopped")

# PLOTTER THREAD → SENDS DATA TO QUEUE
def plot_data():
    print("[plot feeder] started")
    while not stop_event.is_set():
        df = pd.read_csv(NEW_DATA_FILE)
        if df.empty or 'label' not in df.columns:
            stop_event.wait(1)
            continue
        plot_data_queue.put(df)
        stop_event.wait(1)
    print("[plot feeder] stopped")
# MAIN PLOTTING LOOP
def plot_from_queue():
    print("[plotter-main] started")
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 5))
    x_vals = []
    y_vals = []
    while True:
        if not plot_data_queue.empty():
            df = plot_data_queue.get()

            # Append new values
            for idx, row in df.iterrows():
                x_vals.append(len(x_vals))
                y_vals.append(int(row['label']))

            ax.cla()
            ax.plot(x_vals, y_vals, linewidth=2)
            ax.set_title("Live Fraud Detection (0 = Normal, 1 = Fraud)")
            ax.set_xlabel("Time (latest → right side)")
            ax.set_ylabel("Fraud Label")
            # Scroll left as new data arrives
            ax.set_xlim(max(0, len(x_vals) - 50), len(x_vals))
            ax.set_ylim(-0.2, 1.2)
            plt.pause(0.1)

# MAIN
def main():
    ensure_file(NEW_DATA_FILE)

    t1 = threading.Thread(target=writer_thread, args=(NEW_DATA_FILE, WRITE_INTERVAL), daemon=True)
    t2 = threading.Thread(target=predictor_thread, args=(NEW_DATA_FILE, PREDICT_INTERVAL), daemon=True)
    t3 = threading.Thread(target=plot_data, daemon=True)

    t1.start()
    t2.start()
    t3.start()

    plot_from_queue()

if __name__ == "__main__":
    main()

