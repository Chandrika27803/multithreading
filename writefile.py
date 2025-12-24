import time
import datetime
import random
filename = "temp.dat"
print("Starting temperature writer... Press Ctrl+C to stop.")
try:
    with open(filename, "a") as file:
        while True:
            # Current date and time
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            # Simulated temperature
            temperature = round(random.uniform(20.0, 35.0), 2)
            # Write line to file
            file.write(f"{date_str}, {time_str}, {temperature} °C\n")
            file.flush()  # Ensure data is written immediately
            print(f"Written -> {date_str}, {time_str}, {temperature} °C")
            time.sleep(2)
except KeyboardInterrupt:
    print("\nWriter stopped by user.")
