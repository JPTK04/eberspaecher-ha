import logging
import aiohttp
import json

_LOGGER = logging.getLogger(__name__)

API_BASE_URL = "https://myeberspaecher.com/escw-application-server/rest/v1"


class EberspaecherAPI:
    def __init__(self, username, password, session: aiohttp.ClientSession):
        self._username = username
        self._password = password
        self._session = session
        self._token = None
        self._headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/json"
        }

    async def login(self):
        """Loggt sich per Header-Auth ein."""
        url = f"{API_BASE_URL}/authenticate"
        auth_headers = self._headers.copy()
        auth_headers["escw-auth-email"] = self._username
        auth_headers["escw-auth-password"] = self._password

        if "Content-Type" in auth_headers:
            del auth_headers["Content-Type"]

        try:
            async with self._session.post(url, headers=auth_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self._token = data.get("token")
                    return True
                _LOGGER.error(f"Login fehlgeschlagen: {response.status}")
                return False
        except Exception as e:
            _LOGGER.error(f"Verbindungsfehler Login: {e}")
            return False

    async def get_devices(self):
        """Holt die Geräteliste."""
        if not self._token:
            if not await self.login():
                return []

        url = f"{API_BASE_URL}/calls"
        params = {"fetchHeater": "FULL", "email": "CURRENT", "page": "0", "size": "5"}

        headers = self._headers.copy()
        headers["escw-auth-token"] = self._token

        try:
            async with self._session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("content", [])
                return []
        except Exception as e:
            _LOGGER.error(f"Fehler get_devices: {e}")
            return []

    async def get_diagnostics(self, imei):
        """Holt die Heartbeat-Daten (Spannung, RSSI)."""
        if not self._token:
            await self.login()

        url = f"{API_BASE_URL}/heartbeat/{imei}/latest"

        headers = self._headers.copy()
        headers["escw-auth-token"] = self._token

        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                _LOGGER.debug(f"Heartbeat Status: {response.status}")
                return {}
        except Exception as e:
            _LOGGER.error(f"Exception get_diagnostics: {e}")
            return {}

    async def set_state(self, imei, mode, runtime=30):
        """Schaltet die Heizung (HEATING, VENTILATION, OFF)."""
        if not self._token:
            await self.login()

        url = f"{API_BASE_URL}/calls/{imei}/heaters/1"
        headers = self._headers.copy()
        headers["escw-auth-token"] = self._token

        if mode == "OFF":
            payload = {
                "operationMode": "OFF",
                "temperatureLowering": "OFF",
                "altitudeFunction": "OFF"
            }
        else:
            payload = {
                "operationMode": mode,
                "runtime": runtime,
                "remainingRuntime": 0,
                "temperatureLowering": None,
                "altitudeFunction": None
            }

        try:
            async with self._session.put(url, json=payload, headers=headers) as response:
                if response.status in [200, 204]:
                    return True
                error_text = await response.text()
                _LOGGER.error(f"Fehler Schalten ({response.status}): {error_text}")
                return False
        except Exception as e:
            _LOGGER.error(f"Exception Schalten: {e}")
            return False