# parallel_io.py
import os
import re
import sys
import time
import random
import datetime
import threading
from collections import deque
FILENAME = "temp.dat"
WRITE_INTERVAL = 2          # seconds between writes
ANALYSIS_REFRESH = 30       # seconds between average prints
stop_event = threading.Event()

# ---------- Utilities ----------
LINE_RE = re.compile(
    r'^\s*(\d{4}-\d{2}-\d{2})\s*,\s*'
    r'(\d{2}:\d{2}:\d{2})\s*,\s*'
    r'([+-]?\d+(?:\.\d+)?)'
    r'(?:\s*[°]?[CFK]?\s*)?$'
)

def parse_line(line: str):
    """
    Accepts lines like:
      '2025-11-11, 10:46:01, 27.83 °C'
      '2025-11-11,10:46:01,27.83'
    Returns (datetime, float) or (None, None) if it doesn't parse.
    """
    m = LINE_RE.match(line.strip())
    if not m:
        return None, None
    date_str, time_str, temp_str = m.groups()
    try:
        dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        temp = float(temp_str)
        # Ignore future-dated rows (clock issues)
        if dt > datetime.datetime.now() + datetime.timedelta(minutes=5):
            return None, None
        return dt, temp
    except Exception:
        return None, None

def ensure_file(path: str):
    if not os.path.exists(path):
        open(path, "w").close()

# ---------- Writer Thread ----------
def writer_thread(filename: str, interval: int):
    print("[writer] started")
    try:
        with open(filename, "a", encoding="utf-8") as f:
            while not stop_event.is_set():
                now = datetime.datetime.now()
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H:%M:%S")
                temperature = round(random.uniform(20.0, 35.0), 2)  # simulate sensor
                line = f"{date_str}, {time_str}, {temperature} °C\n"
                f.write(line)
                f.flush()
                print(f"[writer] {line.strip()}")
                stop_event.wait(interval)
    except Exception as e:
        print(f"[writer] ERROR: {e}", file=sys.stderr)
    finally:
        print("[writer] stopped")

# ---------- Reader Thread (tail -f) ----------
def reader_thread(filename: str):
    print("[reader] started")
    ensure_file(filename)
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as fp:
            fp.seek(0, os.SEEK_END)  # only show new lines
            while not stop_event.is_set():
                line = fp.readline()
                if line:
                    print(f"[reader] {line.strip()}")
                else:
                    # Handle truncation/rotation: if our position > file size, seek to start
                    try:
                        size = os.path.getsize(filename)
                        if fp.tell() > size:
                            fp.seek(0, os.SEEK_END)
                    except FileNotFoundError:
                        pass
                    stop_event.wait(1)
    except Exception as e:
        print(f"[reader] ERROR: {e}", file=sys.stderr)
    finally:
        print("[reader] stopped")

# ---------- Analyzer Thread ----------
class RollingAnalyzer:
    def __init__(self, filename: str, refresh_s: int = ANALYSIS_REFRESH):
        self.filename = filename
        self.refresh_s = refresh_s
        self.data_12h = deque()  # (timestamp, temp)
        ensure_file(filename)
    def prune_old(self, now: datetime.datetime):
        cutoff = now - datetime.timedelta(hours=12)
        dq = self.data_12h
        while dq and dq[0][0] < cutoff:
            dq.popleft()
    def window_avg(self, hours: int, now: datetime.datetime):
        dq = self.data_12h
        if not dq:
            return None, 0
        cutoff = now - datetime.timedelta(hours=hours)
        total = 0.0
        count = 0
        for ts, temp in reversed(dq):
            if ts < cutoff:
                break
            total += temp
            count += 1
        if count == 0:
            return None, 0
        return total / count, count
    def fmt(self, avg, n):
        return "n/a" if avg is None else f"{avg:.2f} °C (n={n})"
    def print_averages(self, now: datetime.datetime):
        a1, n1 = self.window_avg(1, now)
        a6, n6 = self.window_avg(6, now)
        a12, n12 = self.window_avg(12, now)
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[analyzer {ts}] Rolling averages from '{self.filename}':")
        print(f"  • Last 1 hour : {self.fmt(a1, n1)}")
        print(f"  • Last 6 hours: {self.fmt(a6, n6)}")
        print(f"  • Last 12 hrs : {self.fmt(a12, n12)}")
    def load_existing(self):
        total = 0
        try:
            with open(self.filename, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    ts, temp = parse_line(line)
                    if ts is not None:
                        self.data_12h.append((ts, temp))
                        total += 1
            now = datetime.datetime.now()
            self.prune_old(now)
            return total, len(self.data_12h)
        except Exception as e:
            print(f"[analyzer] load_existing ERROR: {e}", file=sys.stderr)
            return 0, 0

    def run(self):
        print("[analyzer] started")
        total, recent = self.load_existing()
        print(f"[analyzer] init: loaded={total}, recent(<=12h)={recent}")
        now = datetime.datetime.now()
        if recent > 0:
            self.print_averages(now)
            last_print = time.time()
        else:
            print("[analyzer] no recent data; will print upon first reading...")
            last_print = 0.0  # force immediate print on first valid line

        try:
            with open(self.filename, "r", encoding="utf-8", errors="ignore") as fp:
                fp.seek(0, os.SEEK_END)
                while not stop_event.is_set():
                    line = fp.readline()
                    if line:
                        ts, temp = parse_line(line)
                        if ts is not None:
                            self.data_12h.append((ts, temp))
                            now = datetime.datetime.now()
                            self.prune_old(now)
                            if last_print == 0.0:
                                self.print_averages(now)
                                last_print = time.time()
                                continue
                    else:
                        # Handle truncation/rotation
                        try:
                            size = os.path.getsize(self.filename)
                            if fp.tell() > size:
                                fp.seek(0, os.SEEK_END)
                        except FileNotFoundError:
                            pass
                        # periodic print
                        if last_print and (time.time() - last_print >= self.refresh_s):
                            self.print_averages(datetime.datetime.now())
                            last_print = time.time()
                        stop_event.wait(1)
        except Exception as e:
            print(f"[analyzer] ERROR: {e}", file=sys.stderr)
        finally:
            print("[analyzer] stopped")

def analyzer_thread(filename: str, refresh_s: int):
    RollingAnalyzer(filename, refresh_s).run()

 

# ---------- Main ----------
def main():
    # Let user override file name optionally: python3 parallel_io.py myfile.dat
    filename = sys.argv[1] if len(sys.argv) > 1 else FILENAME
    ensure_file(filename)
    t_writer = threading.Thread(target=writer_thread, args=(filename, WRITE_INTERVAL), daemon=True)
    t_reader = threading.Thread(target=reader_thread, args=(filename,), daemon=True)
    t_analy = threading.Thread(target=analyzer_thread, args=(filename, ANALYSIS_REFRESH), daemon=True)
    t_writer.start()
    t_reader.start()
    t_analy.start()
    print("\nRunning. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()
        # give threads a moment to exit gracefully
        t_writer.join(timeout=2)
        t_reader.join(timeout=2)
        t_analy.join(timeout=2)
        print("Done.")

if __name__ == "__main__":
    main()
	

