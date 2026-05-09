"""Zyxel NWA Access Point integration for Home Assistant.

Supports NWA50AX, NWA50BE, NWA90AX, NWA90BE and compatible models
in standalone mode (not managed via Nebula cloud).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, DEFAULT_SCAN_INTERVAL, DOMAIN
from .nwa_api import ZyxelNWAAuthError, ZyxelNWAClient, ZyxelNWAConnectionError

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Zyxel NWA integration from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    client = ZyxelNWAClient(host, username, password)

    try:
        await hass.async_add_executor_job(client.login)
    except ZyxelNWAAuthError as ex:
        _LOGGER.error("Authentication failed for %s: %s", host, ex)
        raise ConfigEntryNotReady(f"Cannot authenticate with {host}") from ex
    except ZyxelNWAConnectionError as ex:
        _LOGGER.error("Cannot connect to %s: %s", host, ex)
        raise ConfigEntryNotReady(f"Cannot connect to {host}") from ex

    async def async_update_data() -> dict:
        """Fetch status from the access point."""
        try:
            return await hass.async_add_executor_job(client.get_status)
        except ZyxelNWAAuthError:
            # Session expired – re-login on next poll
            try:
                await hass.async_add_executor_job(client.login)
                return await hass.async_add_executor_job(client.get_status)
            except Exception as ex:
                raise UpdateFailed(f"Re-auth failed: {ex}") from ex
        except ZyxelNWAConnectionError as ex:
            raise UpdateFailed(f"Connection error: {ex}") from ex
        except Exception as ex:
            raise UpdateFailed(f"Unexpected error: {ex}") from ex

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        client: ZyxelNWAClient = entry_data.get("client")
        if client:
            await hass.async_add_executor_job(client.logout)
    return unload_ok
