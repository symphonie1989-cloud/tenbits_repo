"""Binary sensors for Zyxel NWA Access Points."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([NWAConnectivitySensor(coordinator, entry, client)])


class NWAConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    """Reports whether the AP is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:router-wireless"

    def __init__(self, coordinator, entry: ConfigEntry, client) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_name = f"Zyxel NWA {entry.data['host']} Online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Zyxel {client.model or 'NWA'} ({entry.data['host']})",
            manufacturer="Zyxel",
            model=client.model or "NWA Series",
            sw_version=client.firmware,
            configuration_url=entry.data["host"],
        )

    @property
    def is_on(self) -> bool:
        """True when the last update succeeded."""
        return self.coordinator.last_update_success
