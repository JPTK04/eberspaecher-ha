import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN
from .api import EberspaecherAPI


class EberspaecherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eberspächer."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Der erste Schritt: Benutzer gibt Daten ein."""
        errors = {}

        if user_input is not None:
            # 1. Teste die Eingaben
            session = async_get_clientsession(self.hass)
            api = EberspaecherAPI(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                session
            )

            login_ok = await api.login()

            if login_ok:
                # 2. Speichere die Konfiguration
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data=user_input
                )
            else:
                errors["base"] = "invalid_auth"

        # Zeige das Formular an
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )