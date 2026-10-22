# air_pm - Air Particle Monitor

This is a raspberry pi based indoor air particle monitor using the **Adafruit module PMSA300i sensor**. The python code uses the threading module to schedule and sample the sensors every 15 seconds. The collected data is forwarded via http send request to a seperate web server that then inserts into a MySQL database.

## Uploads

`uploader.py` sends readings to `https://shack.pythonanywhere.com/airdata` every 3 minutes with an
`X-Upload-Token` header. The token is read from `/home/pi/.airdata_token`, which is **not** in this
repository; the website keeps the same value. If an upload fails, the readings stay queued (up to
24 hours) and are retried.

## Updating the Pi

1. Change and test on the Mac (`pytest`), commit, push.
2. `ssh rp`, then `cd ~/air_pm && git pull`.
3. Restart the logger: `sudo reboot`.

`error_summary.py` (run on the Mac) copies the Pi's `error_info.log` and summarizes errors by day.
