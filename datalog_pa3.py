# Air Data Log program by Mark Shackelford - Testing new ideas - 2023-07-30
# Testing long form data collection technique
# Testing threading and use of control file to gracefully stop.

import board
import busio
from adafruit_pm25.i2c import PM25_I2C
from adafruit_bme280 import basic as adafruit_bme280
from datetime import datetime
import logging
import threading
import json
import requests
import os

# Define a global flag to signal the program to stop sampling
stop_sampling_flag = threading.Event()

logging.basicConfig(filename='/home/pi/air_pm/error_info.log', format='%(asctime)s %(levelname)s:%(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.WARNING)
logging.warning(f'********** Script Startup *************\n')
reset_pin = None
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
pm25 = PM25_I2C(i2c, reset_pin)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
airdata_list = []

def sample_sensor_data():
    # code to sample and add new sensor data
    global airdata_list
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
    
    # Loop through the data and create dictionaries and add to list

    for i in range(len(measurements)):
        data_dict = {
            "Timestamp": timestamp,
            "Measurement": measurements[i],
            "Value": values[i]
        }
        airdata_list.append(data_dict)

    if len(airdata_list) >= 60:
        # update db and empty airdata_list
        jdata = json.dumps({'mydata': airdata_list})
        newHeaders = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        try:
            response = requests.post('https://shack.pythonanywhere.com/airdata',
                        data=jdata,
                        headers=newHeaders, timeout=5)
            response.raise_for_status()  # Raise an exception for non-2xx status
        except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
            logging.warning(f" An error occurred: {e}")
                
        airdata_list = []

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
