"""API client for Zyxel NWA Access Points (standalone mode)."""
from __future__ import annotations
import logging
import requests
import urllib3

_LOGGER = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZyxelNWAAuthError(Exception):
    pass

class ZyxelNWAConnectionError(Exception):
    pass

class ZyxelNWAAPIError(Exception):
    pass

class ZyxelNWAClient:
    def __init__(self, host, username, password):
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._session.verify = False
        self._session.headers.update({"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"})
        self._authenticated = False
        self._model = "Unknown"
        self._firmware = "Unknown"
        self._mac = "Unknown"

    def login(self):
        url = f"{self._host}/cgi-bin/DAL?oid=login"
        try:
            resp = self._session.post(url, data={"loginusr": self._username, "loginpwd": self._password}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError as ex:
            raise ZyxelNWAConnectionError(f"Cannot reach {self._host}") from ex
        except requests.exceptions.Timeout:
            raise ZyxelNWAConnectionError("Timeout")
        except Exception as ex:
            raise ZyxelNWAConnectionError(str(ex)) from ex
        if data.get("result") == "ZCFG_SUCCESS" or resp.status_code == 200:
            self._authenticated = True
            self._fetch_device_info()
            return True
        raise ZyxelNWAAuthError("Invalid credentials")

    def logout(self):
        if not self._authenticated:
            return
        try:
            self._session.get(f"{self._host}/cgi-bin/DAL?oid=logout", timeout=5)
        except Exception:
            pass
        self._authenticated = False

    def ensure_logged_in(self):
        if not self._authenticated:
            self.login()

    def _get(self, oid):
        url = f"{self._host}/cgi-bin/DAL?oid={oid}"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as ex:
            self._authenticated = False
            raise ZyxelNWAConnectionError(str(ex)) from ex
        except Exception as ex:
            raise ZyxelNWAAPIError(str(ex)) from ex

    def _post(self, oid, payload=None):
        url = f"{self._host}/cgi-bin/DAL?oid={oid}"
        try:
            resp = self._session.post(url, data=payload or {}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as ex:
            raise ZyxelNWAAPIError(str(ex)) from ex

    def _fetch_device_info(self):
        try:
            data = self._get("dashboard")
            obj = data.get("Object", [{}])
            o = obj[0] if isinstance(obj, list) and obj else (obj or {})
            self._model = o.get("ModelName", o.get("Model", "Unknown"))
            self._firmware = o.get("FWVersion", o.get("Firmware", "Unknown"))
            self._mac = o.get("LanMac", o.get("MACAddr", "Unknown"))
        except Exception:
            pass

    def get_status(self):
        self.ensure_logged_in()
        result = {"model": self._model, "firmware": self._firmware, "mac": self._mac}
        try:
            dash = self._get("dashboard")
            obj = dash.get("Object", [{}])
            o = obj[0] if isinstance(obj, list) and obj else (obj or {})
            result["cpu_usage"] = o.get("CPUUsage")
            result["memory_usage"] = o.get("MemUsage", o.get("MemoryUsage"))
            result["uptime"] = o.get("Uptime", o.get("SystemUptime"))
            result["temperature"] = o.get("Temperature")
            if o.get("ModelName"):
                self._model = o["ModelName"]
                result["model"] = self._model
            if o.get("FWVersion"):
                self._firmware = o["FWVersion"]
                result["firmware"] = self._firmware
        except Exception as ex:
            _LOGGER.debug("dashboard fetch failed: %s", ex)
        try:
            sta = self._get("stalist")
            stations = sta.get("Object", [])
            result["connected_clients"] = len(stations) if isinstance(stations, list) else 0
        except Exception:
            result["connected_clients"] = 0
        try:
            wlan = self._get("wlan_bss")
            ssids = wlan.get("Object", [])
            result["ssid_count"] = len(ssids) if isinstance(ssids, list) else 0
        except Exception:
            result["ssid_count"] = 0
        return result

    def reboot(self):
        self.ensure_logged_in()
        try:
            data = self._post("reboot")
            return data.get("result") in ("ZCFG_SUCCESS", "ok", "success")
        except Exception as ex:
            _LOGGER.error("Reboot failed: %s", ex)
            return False

    @property
    def model(self):
        return self._model

    @property
    def firmware(self):
        return self._firmware

    @property
    def mac(self):
        return self._mac
