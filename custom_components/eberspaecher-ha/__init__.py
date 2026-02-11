from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, DEFAULT_RUNTIME, MODE_HEATING
from .api import EberspaecherAPI

# Diese Plattformen laden wir (Schalter, Auswahl, Nummernfeld, Sensoren)
PLATFORMS = ["switch", "select", "number", "sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup der Integration."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    api = EberspaecherAPI(entry.data["username"], entry.data["password"], session)

    # Wir speichern API und Einstellungen in einem Dictionary
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "settings": {
            "mode": MODE_HEATING,      # Standard: Heizen
            "runtime": DEFAULT_RUNTIME # Standard: 30 Min
        }
    }

    # Lade alle Plattformen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entfernen der Integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok