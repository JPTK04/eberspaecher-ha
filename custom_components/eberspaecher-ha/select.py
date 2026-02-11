from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, MODE_HEATING, MODE_VENTILATION

# Mapping für schöne Namen in der UI
MODE_MAP = {
    "Heizen": MODE_HEATING,
    "Lüften": MODE_VENTILATION
}
# Umgekehrtes Mapping für interne Logik
REVERSE_MODE_MAP = {v: k for k, v in MODE_MAP.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup der Select Entität."""
    # Wir holen uns das Daten-Objekt aus __init__.py
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    settings = data["settings"]

    # Wir brauchen die Geräte-ID (IMEI)
    devices = await api.get_devices()
    entities = []

    for device in devices:
        entities.append(EberspaecherModeSelect(api, device, settings))

    async_add_entities(entities)


class EberspaecherModeSelect(SelectEntity):
    def __init__(self, api, device, settings):
        self._api = api
        self._device = device
        self._settings = settings
        self._imei = device.get("imei")
        self._attr_name = f"{device.get('name', 'Eberspächer')} Modus"
        self._attr_unique_id = f"{self._imei}_mode_select"
        self._attr_options = list(MODE_MAP.keys())  # ["Heizen", "Lüften"]
        self._attr_icon = "mdi:cog-transfer"

        # Initialer Status aus den Settings
        current_mode = settings.get("mode", MODE_HEATING)
        self._attr_current_option = REVERSE_MODE_MAP.get(current_mode, "Heizen")

    async def async_select_option(self, option: str) -> None:
        """Wird aufgerufen, wenn der User eine Option wählt."""
        internal_mode = MODE_MAP[option]

        # 1. Speichern in den globalen Settings
        self._settings["mode"] = internal_mode

        # 2. UI aktualisieren
        self._attr_current_option = option
        self.async_write_ha_state()