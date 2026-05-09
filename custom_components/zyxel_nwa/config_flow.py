"""Config flow for Zyxel NWA."""
from __future__ import annotations
import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_HOST, DEFAULT_USERNAME, DOMAIN
from .nwa_api import ZyxelNWAAuthError, ZyxelNWAClient, ZyxelNWAConnectionError

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
})


class ZyxelNWAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
        VERSION = 1

    async def async_step_user(self, user_input=None):
                errors = {}
                if user_input is not None:
                                host = user_input[CONF_HOST].strip()
                                if not host.startswith("http"):
                                                    host = f"https://{host}"
                                                user_input[CONF_HOST] = host.rstrip("/")
                                try:
                                                    client = ZyxelNWAClient(user_input[CONF_HOST], user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                                                    await self.hass.async_add_executor_job(client.login)
                                                    await self.hass.async_add_executor_job(client.logout)
                                                    return self.async_create_entry(title=f"Zyxel NWA ({user_input[CONF_HOST]})", data=user_input)
except ZyxelNWAAuthError:
                errors["base"] = "invalid_auth"
except ZyxelNWAConnectionError:
                errors["base"] = "cannot_connect"
except Exception:
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
