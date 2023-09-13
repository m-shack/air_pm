# air_pm - Air Particle Monitor

This is a raspberry pi based indoor air particle monitor using the **Adafruit module PMSA300i sensor**. The python code uses the threading module to schedule and sample the sensors every 15 seconds. The collected data is forwarded via http send request to a seperate web server that then inserts into a MySQL database.
