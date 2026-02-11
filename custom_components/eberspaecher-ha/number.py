from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, DEFAULT_RUNTIME


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup der Number Plattform."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    settings = data["settings"]

    devices = await api.get_devices()
    entities = []

    for device in devices:
        entities.append(EberspaecherRuntimeNumber(api, device, settings))

    async_add_entities(entities)


class EberspaecherRuntimeNumber(NumberEntity):
    def __init__(self, api, device, settings):
        self._api = api
        self._device = device
        self._settings = settings
        self._imei = device.get("imei")
        self._attr_name = f"{device.get('name', 'Eberspächer')} Laufzeit"
        self._attr_unique_id = f"{self._imei}_runtime_number"

        # Grenzen basierend auf deiner HAR Datei (10-120 Min)
        self._attr_native_min_value = 10
        self._attr_native_max_value = 120
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "min"
        self._attr_icon = "mdi:timer-outline"

    @property
    def name(self):
        return self._attr_name

    @property
    def native_value(self):
        """Liest den aktuellen Wert aus dem globalen Speicher."""
        return self._settings.get("runtime", DEFAULT_RUNTIME)

    async def async_set_native_value(self, value: float) -> None:
        """Speichert den neuen Wert im globalen Speicher."""
        # Wir senden noch nichts an die API, das passiert erst beim Einschalten!
        self._settings["runtime"] = int(value)
        self.async_write_ha_state()