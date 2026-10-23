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

## Setting up a new Pi

Last done 2026-10-23 on a Raspberry Pi 4 (Raspberry Pi OS Lite, trixie, Python 3.13).

1. Raspberry Pi Imager: Raspberry Pi OS Lite; user `pi`; Wi-Fi; time zone `America/Chicago`
   (the website stores Central time); SSH with the Mac's public key.
2. On the Pi:
   - `sudo raspi-config nonint do_i2c 0`
   - `sudo apt update && sudo apt install -y git python3-venv`
   - `git clone https://github.com/m-shack/air_pm.git ~/air_pm`
   - `python3 -m venv --system-site-packages ~/air_pm/venv`
   - `~/air_pm/venv/bin/pip install -r ~/air_pm/requirements.txt`
   - Add the line in `crontab_reboot_autostart.txt` with `crontab -e`.
3. Copy the upload token from PythonAnywhere to `/home/pi/.airdata_token` (mode 600), then `sudo reboot`.
