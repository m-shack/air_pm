# Upload readings to the Shack Air website, keeping any that fail so they are retried.
# Added 2026-10-22. Kept free of sensor/hardware imports so it can be tested on the Mac.
# The Pi runs Python 3.13 (Raspberry Pi OS trixie, rebuilt 2026-10-23).
#
# The upload token is read from a file that is NOT in git (this repo is public):
#   /home/pi/.airdata_token   (one line: the same token as ~/.airdata_token on PythonAnywhere)

import json
import logging

import requests

UPLOAD_URL = "https://shack.pythonanywhere.com/airdata"
TOKEN_FILE = "/home/pi/.airdata_token"
SAMPLES_PER_UPLOAD = 12     # normal upload every 3 minutes (12 samples, 15 s apart)
MAX_ROWS_PER_POST = 1680    # one hour of readings (7 measurements x 240 samples)
MAX_PENDING_ROWS = 40320    # one day; beyond this the oldest readings are dropped


def read_token(path=TOKEN_FILE):
    try:
        with open(path) as f:
            token = f.read().strip()
    except FileNotFoundError:
        token = ""
    if not token:
        logging.warning(f" No upload token in {path}; uploading without a token")
    return token or None


class Uploader:
    def __init__(self, token=None, url=UPLOAD_URL, session=requests):
        self.url = url
        self.session = session
        self.pending = []
        self.new_rows = 0       # rows added since the last upload attempt
        self.new_samples = 0    # add() calls (one per 15-second sample) since then
        self.last_ok = True
        self.headers = {"Content-type": "application/json", "Accept": "text/plain"}
        if token:
            self.headers["X-Upload-Token"] = token

    def add(self, rows):
        self.pending.extend(rows)
        self.new_rows += len(rows)
        self.new_samples += 1
        overflow = len(self.pending) - MAX_PENDING_ROWS
        if overflow > 0:
            del self.pending[:overflow]
            logging.warning(f" Upload backlog full; dropped {overflow} oldest readings")

    def due(self):
        """Every 3 minutes normally; while the website is down, retry only every 3 minutes;
        right after it comes back, keep sending until the backlog is cleared."""
        backlog = len(self.pending) > self.new_rows    # older readings than the latest few are waiting
        return self.new_samples >= SAMPLES_PER_UPLOAD or (self.last_ok and backlog)

    def send(self):
        """Upload the oldest pending readings. Returns True if the website accepted them."""
        self.new_rows = self.new_samples = 0
        batch = self.pending[:MAX_ROWS_PER_POST]
        try:
            response = self.session.post(self.url, data=json.dumps({"mydata": batch}),
                                         headers=self.headers, timeout=5)
            response.raise_for_status()  # Raise an exception for non-2xx status
        except requests.exceptions.RequestException as e:
            logging.warning(f" An error occurred: {e} ({len(self.pending)} readings waiting)")
            self.last_ok = False
            return False
        self.last_ok = True
        del self.pending[:len(batch)]
        if self.pending:
            logging.warning(f" Upload recovered; {len(self.pending)} readings still waiting")
        return True
