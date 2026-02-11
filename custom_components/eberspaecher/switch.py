from datetime import timedelta
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup Switch."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    settings = data["settings"]

    devices = await api.get_devices()
    entities = []
    for dev in devices:
        entities.append(EberspaecherSwitch(api, dev, settings))

    async_add_entities(entities, True)


class EberspaecherSwitch(SwitchEntity):
    def __init__(self, api, device, settings):
        self._api = api
        self._device = device
        self._settings = settings  # Zugriff auf die globalen Settings
        self._id = device.get("imei")
        self._name = f"{device.get('name', 'Eberspächer')} Heizung"
        self._is_on = False

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"eberspaecher_{self._id}_switch"

    @property
    def is_on(self):
        return self._is_on

    @property
    def icon(self):
        # Icon ändert sich je nach Modus
        if self._is_on:
            if self._settings["mode"] == "VENTILATION":
                return "mdi:fan"
            return "mdi:radiator"
        return "mdi:radiator-off"

    async def async_update(self):
        """Status prüfen."""
        devices = await self._api.get_devices()
        for dev in devices:
            if dev.get("imei") == self._id:
                # Wir prüfen heaterState oder heaters[0].heaterState
                # Pass das hier an deine JSON Struktur an!
                heaters = dev.get("heaters", [{}])
                heater = heaters[0] if heaters else {}
                state = heater.get("heaterState", "OFF")

                # Prüfen ob an (HEATING, VENTILATION, etc.)
                self._is_on = state not in ["OFF", "DEACTIVATION_REQUESTED"]

    async def async_turn_on(self, **kwargs):
        """Einschalten mit den gewählten Settings."""
        # Hole Modus und Laufzeit aus den Settings (die von select.py gesetzt wurden)
        mode = self._settings.get("mode", "HEATING")
        runtime = self._settings.get("runtime", 30)

        _LOGGER.info(f"Starte Standheizung: Modus={mode}, Zeit={runtime}m")

        success = await self._api.set_state(self._id, mode, runtime=runtime)
        if success:
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Ausschalten."""
        success = await self._api.set_state(self._id, "OFF")
        if success:
            self._is_on = False
            self.async_write_ha_state()