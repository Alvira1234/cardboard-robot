"""Small HTTPS client for the phone-control Pages Functions API."""
import json
import time


class CloudClient:
    def __init__(self, ssid, password, api_base, token, poll_interval_ms=5000):
        self.ssid = ssid
        self.password = password
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.poll_interval_ms = poll_interval_ms
        self.wlan = None
        self.next_poll = 0
        self.last_status = None
        self.last_error = None

    def connect(self):
        import network
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            self.wlan.connect(self.ssid, self.password)
            deadline = time.ticks_add(time.ticks_ms(), 15000)
            while not self.wlan.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
                time.sleep_ms(250)
        if not self.wlan.isconnected():
            raise OSError("Wi-Fi connection timed out")

    def _request(self, path, body=None):
        import urequests
        headers = {"Authorization": "Bearer " + self.token}
        response = None
        try:
            if body is None:
                response = urequests.get(self.api_base + path, headers=headers)
            else:
                headers["Content-Type"] = "application/json"
                response = urequests.post(
                    self.api_base + path, headers=headers, data=json.dumps(body))
            if response.status_code != 200:
                raise OSError("Cloud API returned " + str(response.status_code))
            return response.json()
        finally:
            if response is not None:
                response.close()

    def poll(self, now):
        if time.ticks_diff(now, self.next_poll) < 0:
            return None
        self.next_poll = time.ticks_add(now, self.poll_interval_ms)
        try:
            status = self._request("/api/device/poll")
            self.last_status = status
            self.last_error = None
            return status
        except Exception as error:
            self.last_error = str(error)
            return None

    def report(self, payload):
        try:
            status = self._request("/api/device/report", payload)
            self.last_status = status
            self.last_error = None
            return status
        except Exception as error:
            self.last_error = str(error)
            return None
