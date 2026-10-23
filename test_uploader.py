# Tests for uploader.py with a fake website (no network or Pi hardware needed). Run with: pytest
import json
import logging

import requests

import uploader
from uploader import Uploader, read_token


class FakeResponse:
    def __init__(self, status):
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} Server Error")


class FakeSite:
    """Records posts; 'down' makes it answer 500, 'timeout' makes it time out."""

    def __init__(self):
        self.mode = "up"
        self.received = []
        self.headers = []

    def post(self, url, data, headers, timeout):
        self.headers.append(headers)
        if self.mode == "timeout":
            raise requests.exceptions.ReadTimeout("Read timed out")
        if self.mode == "down":
            return FakeResponse(500)
        self.received.extend(json.loads(data)["mydata"])
        return FakeResponse(200)


def sample(i):
    """One 15-second sample: 5 rows."""
    return [{"Timestamp": f"t{i}", "Measurement": m, "Value": i} for m in ("a", "b", "c", "d", "e")]


def run(up, site, samples, start=0):
    for i in range(start, start + samples):
        up.add(sample(i))
        if up.due():
            up.send()


def test_uploads_every_12_samples():
    site = FakeSite()
    up = Uploader(token="secret", session=site)
    run(up, site, 24)
    assert len(site.headers) == 2 and len(site.received) == 120 and up.pending == []
    assert site.headers[0]["X-Upload-Token"] == "secret"


def test_no_token_header_without_token():
    site = FakeSite()
    up = Uploader(token=None, session=site)
    run(up, site, 12)
    assert "X-Upload-Token" not in site.headers[0]


def test_outage_keeps_data_retries_every_3_minutes_then_catches_up():
    site = FakeSite()
    up = Uploader(session=site)
    site.mode = "down"
    run(up, site, 240)                      # one hour down
    assert len(site.headers) == 20          # one attempt per 3 minutes, not every 15 s
    assert len(up.pending) == 1200 and site.received == []
    site.mode = "up"
    run(up, site, 24, start=240)
    # Everything was delivered in order; only the newest few rows wait for the next upload.
    sent_and_waiting = [r["Timestamp"] for r in site.received + up.pending]
    assert sent_and_waiting == [f"t{i}" for i in range(264) for _ in range(5)]
    assert len(up.pending) < 60


def test_large_backlog_sent_in_chunks():
    site = FakeSite()
    up = Uploader(session=site)
    site.mode = "down"
    run(up, site, 720)                      # three hours down
    site.mode = "up"
    attempts_before = len(site.headers)
    run(up, site, 11, start=720)
    assert len(site.headers) == attempts_before    # waits for the next 3-minute retry
    run(up, site, 4, start=731)                     # retry, then quick chunks every 15 s
    assert len(site.headers) - attempts_before == 4
    assert all(set(r) == {"Timestamp", "Measurement", "Value"} for r in site.received)
    assert len(site.received) == 3600 + 15 * 5 - len(up.pending)
    assert len(up.pending) < 60


def test_timeout_is_retried_too():
    site = FakeSite()
    up = Uploader(session=site)
    site.mode = "timeout"
    run(up, site, 12)
    assert len(up.pending) == 60
    site.mode = "up"
    run(up, site, 12, start=12)
    assert len(site.received) == 120


def test_backlog_is_capped(caplog):
    site = FakeSite()
    up = Uploader(session=site)
    site.mode = "down"
    with caplog.at_level(logging.WARNING):
        up.add([{"Timestamp": "x"}] * (uploader.MAX_PENDING_ROWS + 10))
    assert len(up.pending) == uploader.MAX_PENDING_ROWS
    assert "dropped 10 oldest" in caplog.text


def test_error_log_wording_still_matches_error_summary(caplog):
    site = FakeSite()
    up = Uploader(session=site)
    site.mode = "down"
    with caplog.at_level(logging.WARNING):
        run(up, site, 12)
    assert "An error occurred: 500 Server Error" in caplog.text


def test_read_token(tmp_path):
    f = tmp_path / "tok"
    f.write_text("abc123\n")
    assert read_token(str(f)) == "abc123"
    assert read_token(str(tmp_path / "missing")) is None
