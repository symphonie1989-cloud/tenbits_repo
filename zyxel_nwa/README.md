"""API client for Zyxel NWA Access Points (standalone mode).

The NWA series uses a CGI-based JSON API at /cgi-bin/DAL?oid=<endpoint>.
Authentication is session-cookie based. The session cookie is returned
after a successful POST to the login endpoint.
"""
from __future__ import annotations

import logging
import ssl
from typing import Any

import requests
import urllib3

_LOGGER = logging.getLogger(__name__)

# Suppress SSL warnings for self-signed certs (Zyxel APs use self-signed)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ZyxelNWAAuthError(Exception):
    """Raised when authentication fails."""


class ZyxelNWAConnectionError(Exception):
    """Raised when the device cannot be reached."""


class ZyxelNWAAPIError(Exception):
    """Raised when the API returns an unexpected response."""


class ZyxelNWAClient:
    """HTTP client for Zyxel NWA access points in standalone mode.

    The web interface uses a REST-like CGI API:
      POST /cgi-bin/DAL?oid=login          → sets Session cookie
      GET  /cgi-bin/DAL?oid=<resource>     → returns JSON data
      POST /cgi-bin/DAL?oid=<resource>     → modify / action
      GET  /cgi-bin/DAL?oid=logout         → invalidates session
    """

    def __init__(self, host: str, username: str, password: str) -> None:
        self._host = host.rstrip("/")
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._session.verify = False  # self-signed cert
        self._session.headers.update(
            {
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            }
        )
        self._authenticated = False
        self._model: str = "Unknown"
        self._firmware: str = "Unknown"
        self._mac: str = "Unknown"

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self) -> bool:
        """Authenticate and store session cookie. Returns True on success."""
        url = f"{self._host}/cgi-bin/DAL?oid=login"
        payload = {
            "loginusr": self._username,
            "loginpwd": self._password,
        }
        try:
            resp = self._session.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.ConnectionError as ex:
            raise ZyxelNWAConnectionError(f"Cannot reach {self._host}: {ex}") from ex
        except requests.exceptions.Timeout as ex:
            raise ZyxelNWAConnectionError(f"Timeout connecting to {self._host}") from ex
        except Exception as ex:
            raise ZyxelNWAConnectionError(f"Login request failed: {ex}") from ex

        result = data.get("result", "")
        if result == "ZCFG_SUCCESS" or result == "ok" or resp.status_code == 200:
            # Some firmware versions also set a sessionkey
            self._authenticated = True
            _LOGGER.debug("Login successful for %s", self._host)
            # Fetch basic device info right after login
            self._fetch_device_info()
            return True

        _LOGGER.error("Login failed for %s: %s", self._host, data)
        raise ZyxelNWAAuthError(f"Invalid credentials for {self._host}")

    def logout(self) -> None:
        """Invalidate the current session."""
        if not self._authenticated:
            return
        try:
            self._session.get(
                f"{self._host}/cgi-bin/DAL?oid=logout", timeout=5
            )
        except Exception:
            pass
        self._authenticated = False

    def ensure_logged_in(self) -> None:
        """Re-login if the session has expired."""
        if not self._authenticated:
            self.login()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, oid: str) -> dict[str, Any]:
        """GET /cgi-bin/DAL?oid=<oid> and return parsed JSON."""
        url = f"{self._host}/cgi-bin/DAL?oid={oid}"
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as ex:
            self._authenticated = False
            raise ZyxelNWAConnectionError(str(ex)) from ex
        except requests.exceptions.Timeout as ex:
            self._authenticated = False
            raise ZyxelNWAConnectionError("Request timed out") from ex
        except Exception as ex:
            raise ZyxelNWAAPIError(str(ex)) from ex

    def _post(self, oid: str, payload: dict | None = None) -> dict[str, Any]:
        """POST /cgi-bin/DAL?oid=<oid> with optional form payload."""
        url = f"{self._host}/cgi-bin/DAL?oid={oid}"
        try:
            resp = self._session.post(url, data=payload or {}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as ex:
            self._authenticated = False
            raise ZyxelNWAConnectionError(str(ex)) from ex
        except requests.exceptions.Timeout as ex:
            self._authenticated = False
            raise ZyxelNWAConnectionError("Request timed out") from ex
        except Exception as ex:
            raise ZyxelNWAAPIError(str(ex)) from ex

    def _fetch_device_info(self) -> None:
        """Try to read firmware/model info and cache it."""
        try:
            data = self._get("fw_version")
            obj = data.get("Object", [{}])
            if obj:
                o = obj[0] if isinstance(obj, list) else obj
                self._model = o.get("ModelName", o.get("Model", "Unknown"))
                self._firmware = o.get("Firmware", o.get("FWVersion", "Unknown"))
                self._mac = o.get("MACAddr", o.get("LanMac", "Unknown"))
        except Exception as ex:
            _LOGGER.debug("Could not read fw_version: %s", ex)

        # Fallback: try dashboard endpoint
        if self._model == "Unknown":
            try:
                data = self._get("dashboard")
                obj = data.get("Object", [{}])
                if obj:
                    o = obj[0] if isinstance(obj, list) else obj
                    self._model = o.get("ModelName", o.get("Model", "Unknown"))
                    self._firmware = o.get(
                        "FWVersion", o.get("Firmware", "Unknown")
                    )
                    self._mac = o.get("MACAddr", o.get("LanMac", "Unknown"))
            except Exception as ex:
                _LOGGER.debug("Could not read dashboard: %s", ex)

    # ------------------------------------------------------------------
    # Public data methods (called by HA coordinator)
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return a unified status dict for use in HA sensors."""
        self.ensure_logged_in()

        result: dict[str, Any] = {
            "model": self._model,
            "firmware": self._firmware,
            "mac": self._mac,
        }

        # --- Dashboard / system overview ---
        try:
            dash = self._get("dashboard")
            obj = dash.get("Object", [{}])
            o = obj[0] if isinstance(obj, list) and obj else (obj or {})
            result["cpu_usage"] = o.get("CPUUsage")
            result["memory_usage"] = o.get("MemUsage", o.get("MemoryUsage"))
            result["uptime"] = o.get("Uptime", o.get("SystemUptime"))
            result["temperature"] = o.get("Temperature")
            # Update cached identifiers if available
            if o.get("ModelName"):
                self._model = o["ModelName"]
                result["model"] = self._model
            if o.get("FWVersion"):
                self._firmware = o["FWVersion"]
                result["firmware"] = self._firmware
            if o.get("LanMac") or o.get("MACAddr"):
                self._mac = o.get("LanMac", o.get("MACAddr", self._mac))
                result["mac"] = self._mac
        except Exception as ex:
            _LOGGER.debug("dashboard fetch failed: %s", ex)

        # --- Connected clients ---
        try:
            sta = self._get("stalist")
            stations = sta.get("Object", [])
            if isinstance(stations, list):
                result["connected_clients"] = len(stations)
                result["clients"] = stations
            else:
                result["connected_clients"] = 0
                result["clients"] = []
        except Exception as ex:
            _LOGGER.debug("stalist fetch failed: %s", ex)
            result["connected_clients"] = 0
            result["clients"] = []

        # --- WLAN SSIDs ---
        try:
            wlan = self._get("wlan_bss")
            ssids = wlan.get("Object", [])
            if isinstance(ssids, list):
                result["ssid_count"] = len(ssids)
                result["ssids"] = [
                    {
                        "ssid": s.get("SSID", ""),
                        "band": s.get("Band", s.get("BandMode", "")),
                        "enabled": s.get("BSSEnable", s.get("Enable", True)),
                        "security": s.get(
                            "SecurityMode", s.get("AuthMode", "")
                        ),
                    }
                    for s in ssids
                ]
        except Exception as ex:
            _LOGGER.debug("wlan_bss fetch failed: %s", ex)

        # --- Radio channel info ---
        try:
            ch = self._get("channel_status")
            radios = ch.get("Object", [])
            if isinstance(radios, list):
                result["radios"] = [
                    {
                        "band": r.get("Band", ""),
                        "channel": r.get("Channel", r.get("CurChannel")),
                        "tx_power": r.get("TxPower", r.get("TXPower")),
                        "standard": r.get("Standard", r.get("PhyMode", "")),
                    }
                    for r in radios
                ]
        except Exception as ex:
            _LOGGER.debug("channel_status fetch failed: %s", ex)

        return result

    def reboot(self) -> bool:
        """Send reboot command. Returns True if accepted."""
        self.ensure_logged_in()
        try:
            data = self._post("reboot")
            return data.get("result") in ("ZCFG_SUCCESS", "ok", "success")
        except Exception as ex:
            _LOGGER.error("Reboot failed: %s", ex)
            return False

    @property
    def model(self) -> str:
        return self._model

    @property
    def firmware(self) -> str:
        return self._firmware

    @property
    def mac(self) -> str:
        return self._mac
