import time
from datetime import timedelta,datetime
import os

filename="temp.txt"

# Check if file exists
if not os.path.exists(filename):
    open(filename, "w").close()  # create empty file if missing

try:
    with open(filename, "r") as file:
        # Move to end of file initially
        file.seek(0, os.SEEK_END)
        count=1
        temp=0
        avg=0
        #res=[]
        while True:
            line = file.readline()
            if line:
                #print(line)
                s=line.strip().split(',')
                #print(s)
                if s!=['']:
                    time=s[1].strip()
                    nextTime=datetime.now()+timedelta(minutes=1)
                    while datetime.now()<=nextTime:
                        temp+=float(s[2])
                        avg=(temp/count)
                        count+=1
                    print(f"Read -> {nextTime} : Avg => {avg}")
                    #time=nextTime
            #if line:
            #   print(f"Read -> {line.strip()}")
            else:
                time.sleep(1)  # Wait for writer to add new data
except KeyboardInterrupt:
    print("\nReader stopped by user.")
