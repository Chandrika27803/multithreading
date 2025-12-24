import os
import time
import random
import threading
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
from queue import Queue
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
HISTORICAL_FILE = "historical.csv"
NEW_DATA_FILE = "new_data.csv"
WRITE_INTERVAL = 2
PREDICT_INTERVAL = 4
MODEL_RETRAIN_INTERVAL = 60  # Retrain model every 60 seconds instead of every prediction
FILE_COLUMNS = ['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score', 'label']
DATA_LOCK = threading.Lock()  # Lock for file access

# Global variables
stop_event = threading.Event()
plot_data_queue = Queue()
model_cache = None  # Cache the trained model
last_train_time = 0

def ensure_file(path: str):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=FILE_COLUMNS)
        df.to_csv(path, index=False)
    else:
        df = pd.read_csv(path)
        missing = [c for c in FILE_COLUMNS if c not in df.columns]
        if missing:
            logging.warning(f"Repairing corrupted file: {path}")
            df = pd.DataFrame(columns=FILE_COLUMNS)
            df.to_csv(path, index=False)

def train_model():
    global model_cache, last_train_time
    current_time = time.time()
    if model_cache is None or (current_time - last_train_time) > MODEL_RETRAIN_INTERVAL:
        df = pd.read_csv(HISTORICAL_FILE)
        if df.empty:
            return None
        df = df.dropna()
        X = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
        y = df['label']
        model = RandomForestClassifier(n_estimators=80, random_state=42)
        model.fit(X, y)
        model_cache = model
        last_train_time = current_time
        logging.info("Model retrained")
    return model_cache

def writer_thread(filename: str, interval: int):
    logging.info("[writer] started")
    ensure_file(filename)
    while not stop_event.is_set():
        amount_pattern = round(random.uniform(20.0, 100.0), 2)
        frequency = round(random.uniform(1.0, 10.0), 2)
        merchant_risk = random.randint(1, 5)
        time_of_day_score = round(random.uniform(0.0, 1.0), 2)
        line = f"{amount_pattern},{frequency},{merchant_risk},{time_of_day_score},0\n"
        
        with DATA_LOCK:  # Lock for safe appending
            with open(filename, "a", encoding="utf-8") as f:
                f.write(line)
        
        logging.info(f"[writer] wrote: {line.strip()}")
        stop_event.wait(interval)
    logging.info("[writer] stopped")

def predictor_thread(filename: str, interval: int):
    logging.info("[predictor] started")
    ensure_file(filename)
    while not stop_event.is_set():
        with DATA_LOCK:  # Lock for safe reading/writing
            df = pd.read_csv(filename)
        
        if df.empty:
            stop_event.wait(interval)
            continue
        
        df = df.dropna(subset=['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score'])
        model = train_model()
        if model is None:
            stop_event.wait(interval)
            continue
        
        X_new = df[['amount_pattern', 'frequency', 'merchant_risk', 'time_of_day_score']]
        predicted = model.predict(X_new)
        df['label'] = predicted
        
        with DATA_LOCK:  # Lock for safe writing
            df.to_csv(filename, index=False)
        
        logging.info(f"[predictor] updated labels in {filename}")
        stop_event.wait(interval)
    logging.info("[predictor] stopped")

def plot_data():
    logging.info("[plot feeder] started")
    while not stop_event.is_set():
        with DATA_LOCK:  # Lock for safe reading
            df = pd.read_csv(NEW_DATA_FILE)
        
        if df.empty or 'label' not in df.columns:
            stop_event.wait(1)
            continue
        
        plot_data_queue.put(df)
        stop_event.wait(1)
    logging.info("[plot feeder] stopped")

# Enhanced plotting (see details below)
def plot_from_queue():
    logging.info("[plotter-main] started")
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x_vals = []
    y_vals = []
    colors = []
    
    while not stop_event.is_set():
        if not plot_data_queue.empty():
            df = plot_data_queue.get()
            
            for idx, row in df.iterrows():
                x_vals.append(len(x_vals))
                y_vals.append(int(row['label']))
                colors.append('red' if row['label'] == 1 else 'green')  # Color-code fraud
            
            ax.cla()
            ax.scatter(x_vals, y_vals, c=colors, s=50, alpha=0.7, edgecolors='black')  # Scatter plot for visibility
            ax.plot(x_vals, y_vals, color='blue', linewidth=1, alpha=0.5)  # Optional connecting line
            
            ax.set_title("Live Fraud Detection Dashboard", fontsize=16, fontweight='bold')
            ax.set_xlabel("Transaction Index (Latest → Right)", fontsize=12)
            ax.set_ylabel("Fraud Label (0 = Normal, 1 = Fraud)", fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.set_xlim(max(0, len(x_vals) - 50), len(x_vals))
            ax.set_ylim(-0.2, 1.2)
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor='green', label='Normal'), Patch(facecolor='red', label='Fraud')]
            ax.legend(handles=legend_elements, loc='upper right')
            
            plt.tight_layout()
            plt.pause(0.1)
    
    plt.ioff()
    plt.show()

def main():
    ensure_file(HISTORICAL_FILE)
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

