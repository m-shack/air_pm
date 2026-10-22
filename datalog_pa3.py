# Air Data Log program by Mark Shackelford - Testing new ideas - 2023-07-30
# Testing long form data collection technique
# Testing threading and use of control file to gracefully stop.
# 2026-10-22: uploads moved to uploader.py (sends upload token, retries failed batches).

import board
import busio
from adafruit_pm25.i2c import PM25_I2C
from adafruit_bme280 import basic as adafruit_bme280
from datetime import datetime
import logging
import threading
import os

from uploader import Uploader, read_token

# Define a global flag to signal the program to stop sampling
stop_sampling_flag = threading.Event()

logging.basicConfig(filename='/home/pi/air_pm/error_info.log', format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)
logging.warning(f'********** Script Startup *************\n')
reset_pin = None
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
pm25 = PM25_I2C(i2c, reset_pin)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
uploader = Uploader(token=read_token())

def sample_sensor_data():
    # code to sample and add new sensor data
    while True:
        try:
            aqdata = pm25.read()
            temp_c = round(bme280.temperature, 1)
            humidity = round(bme280.relative_humidity, 1)
            pressure = round(bme280.pressure, 1)
            break
        except RuntimeError:
            logging.warning(f" Unable to read from particle sensor, retrying...")
            continue
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    measurements = ['count_03um', 'count_05um', 'temp_c', 'humidity', 'pressure']
    values = [aqdata['particles 03um'], aqdata['particles 05um'], temp_c, humidity, pressure] 
    
    uploader.add([{"Timestamp": timestamp, "Measurement": m, "Value": v}
                  for m, v in zip(measurements, values)])

    # Upload every 3 minutes. Failed uploads stay pending and are retried.
    if uploader.due():
        uploader.send()

    # Check the stop_sampling_flag to see if the program should stop
    if not stop_sampling_flag.is_set():
        # Schedule the next sampling iteration
        threading.Timer(sampling_interval, sample_sensor_data).start()

def check_for_control_file():
    control_file_path = '/home/pi/air_pm/stop.txt'
    if os.path.exists(control_file_path):
        logging.warning(f"********* Stopping the sampling program gracefully...")
        stop_sampling_flag.set()
    else:
        # Schedule the next check after a certain interval
        threading.Timer(5, check_for_control_file).start()

# Define the sampling interval in seconds (15 seconds in this case)
sampling_interval = 15

# Start the initial sampling schedule
sample_sensor_data()

# Start the control file checking
check_for_control_file()
