# readdata.py
import time
import os
filename = "temp.dat"
print("Starting temperature reader... Press Ctrl+C to stop.")
# Check if file exists
if not os.path.exists(filename):
    open(filename, "w").close()  # create empty file if missing
try:
    with open(filename, "r") as file:
        # Move to end of file initially
        file.seek(0, os.SEEK_END)
        while True:
            line = file.readline()
            if line:
                print(f"Read -> {line.strip()}")
            else:
                time.sleep(1)  # Wait for writer to add new data
except KeyboardInterrupt:
    print("\nReader stopped by user.")
