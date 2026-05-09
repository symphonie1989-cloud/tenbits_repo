"""Button entities for Zyxel NWA Access Points."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Zyxel NWA buttons."""
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([NWARebootButton(entry, client)])


class NWARebootButton(ButtonEntity):
    """Button to reboot the access point."""

    _attr_icon = "mdi:restart"

    def __init__(self, entry: ConfigEntry, client) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_reboot"
        self._attr_name = f"Zyxel NWA Reboot ({entry.data['host']})"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Zyxel {client.model or 'NWA'} ({entry.data['host']})",
            manufacturer="Zyxel",
            model=client.model or "NWA Series",
            sw_version=client.firmware,
            configuration_url=entry.data["host"],
        )

    async def async_press(self) -> None:
        """Send reboot command to the AP."""
        _LOGGER.info("Rebooting Zyxel NWA at %s", self._client._host)
        success = await self.hass.async_add_executor_job(self._client.reboot)
        if success:
            _LOGGER.info("Reboot command accepted")
        else:
            _LOGGER.error("Reboot command was not accepted by the device")
