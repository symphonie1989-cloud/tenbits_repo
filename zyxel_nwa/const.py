"""Config flow for Zyxel NWA Access Point integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_HOST, DEFAULT_USERNAME, DOMAIN
from .nwa_api import ZyxelNWAAuthError, ZyxelNWAClient, ZyxelNWAConnectionError

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _normalize_host(host: str) -> str:
    """Ensure the host has an https:// prefix."""
    host = host.strip()
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"https://{host}"
    return host.rstrip("/")


async def _validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate credentials by attempting a login."""
    client = ZyxelNWAClient(
        data[CONF_HOST], data[CONF_USERNAME], data[CONF_PASSWORD]
    )
    await hass.async_add_executor_job(client.login)
    await hass.async_add_executor_job(client.logout)
    model = client.model or "NWA"
    return {"title": f"Zyxel {model} ({data[CONF_HOST]})"}


class ZyxelNWAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Zyxel NWA Access Points."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_HOST] = _normalize_host(user_input[CONF_HOST])

            try:
                info = await _validate_input(self.hass, user_input)
            except ZyxelNWAAuthError:
                errors["base"] = "invalid_auth"
            except ZyxelNWAConnectionError:
                # Try http:// fallback if https failed
                if user_input[CONF_HOST].startswith("https://"):
                    fallback = user_input[CONF_HOST].replace("https://", "http://")
                    try:
                        user_input[CONF_HOST] = fallback
                        info = await _validate_input(self.hass, user_input)
                        return self.async_create_entry(
                            title=info["title"], data=user_input
                        )
                    except Exception:
                        pass
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
