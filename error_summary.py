# Air particle sensor error log summary 
# By Mark Shackelford
# Updated 2026-05-02 with subprocess.run
# Updated 2026-07-30 using generator function to read the log file.
# Run on the Mac: copies error_info.log from the Pi (ssh alias "rp") and summarizes it.

import pandas as pd
from subprocess import run
from datetime import datetime

# get error log from Raspberry Pi
result = run(
    ["scp", "rp:/home/pi/air_pm/error_info.log", "/Users/shackelford/Documents/PythonFiles/air_pm"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("\nError Log copied successfully!")
else:
    print(f"Error: {result.stderr}")

def read_log_lines(file_path):
    """Generator function that yields lines from a log file one by one."""
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            yield line.strip()  # Yields the line and pauses execution

# --- How to use the generator ---

# 1. Initialize the generator (does not read the file yet)
log_stream = read_log_lines("/Users/shackelford/Documents/PythonFiles/air_pm/error_info.log")

# 2. Consume the lines on-demand using a loop

vals = []
dates = []
restarts = []

for log_entry in log_stream:
    if 'Read timed out' in log_entry:
        vals.append('Time_Out')
        dates.append(log_entry[0:10])
    elif 'Max retries' in log_entry:
        vals.append('Max_Retry')
        dates.append(log_entry[0:10])
    elif 'Server Error' in log_entry:
        vals.append('Server_Error')
        dates.append(log_entry[0:10])
    elif 'particle' in log_entry:
        vals.append('Sensor_Retry')
        dates.append(log_entry[0:10])
    elif 'Startup' in log_entry or 'Stop' in log_entry:
        vals.append('Startup')
        dates.append(log_entry[0:10])
        restarts.append(log_entry[0:19])
    elif len(log_entry) < 2:
        continue
    else:
        vals.append('Other')
        dates.append(log_entry[0:10])

lastRestart = restarts[-1]
lastRestart = datetime.strptime(lastRestart, '%m/%d/%Y %H:%M:%S')
restartTimeDelta = (datetime.now() - lastRestart).days
print(f'\nLast RaspberryPi restart was {restartTimeDelta} days ago.\n')

df = pd.DataFrame({'dates': dates, 'values': vals})
df['dates'] = pd.to_datetime(df['dates'])

print(f'The log file contains {len(df)} entries.\n')

pivot_table = df.groupby(['dates', 'values']).size().unstack(fill_value=0)
print(pivot_table.tail())
print()
