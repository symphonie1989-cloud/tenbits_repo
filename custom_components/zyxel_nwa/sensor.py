"""Sensors for Zyxel NWA Access Points."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
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
    """Set up Zyxel NWA sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]

    entities = [
        NWASensor(
            coordinator, entry, client,
            key="connected_clients",
            name="Connected Clients",
            icon="mdi:devices",
            unit="clients",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        NWASensor(
            coordinator, entry, client,
            key="cpu_usage",
            name="CPU Usage",
            icon="mdi:cpu-64-bit",
            unit="%",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        NWASensor(
            coordinator, entry, client,
            key="memory_usage",
            name="Memory Usage",
            icon="mdi:memory",
            unit="%",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        NWASensor(
            coordinator, entry, client,
            key="uptime",
            name="Uptime",
            icon="mdi:clock-outline",
            unit="s",
            device_class=SensorDeviceClass.DURATION,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        NWASensor(
            coordinator, entry, client,
            key="temperature",
            name="Temperature",
            icon="mdi:thermometer",
            unit="°C",
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        NWASensor(
            coordinator, entry, client,
            key="firmware",
            name="Firmware Version",
            icon="mdi:package-up",
        ),
        NWASensor(
            coordinator, entry, client,
            key="model",
            name="Model",
            icon="mdi:router-wireless",
        ),
        NWASensor(
            coordinator, entry, client,
            key="ssid_count",
            name="Active SSIDs",
            icon="mdi:wifi",
            unit="SSIDs",
            state_class=SensorStateClass.MEASUREMENT,
        ),
    ]

    async_add_entities(entities)


def _device_info(entry: ConfigEntry, client) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Zyxel {client.model or 'NWA'} ({entry.data['host']})",
        manufacturer="Zyxel",
        model=client.model or "NWA Series",
        sw_version=client.firmware,
        configuration_url=entry.data["host"],
    )


class NWASensor(CoordinatorEntity, SensorEntity):
    """A sensor reading a single key from the coordinator data."""

    def __init__(
        self,
        coordinator,
        entry: ConfigEntry,
        client,
        key: str,
        name: str,
        icon: str = "mdi:router-wireless",
        unit: str | None = None,
        device_class=None,
        state_class=None,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"Zyxel NWA {name}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = _device_info(entry, client)

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get(self._key)
        # Parse uptime strings like "3d 2h 15m" → seconds
        if self._key == "uptime" and isinstance(val, str):
            return _parse_uptime(val)
        return val

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success


def _parse_uptime(uptime_str: str) -> int | None:
    """Convert '3d 2h 15m 4s' style strings to seconds."""
    import re
    total = 0
    try:
        for val, unit in re.findall(r"(\d+)\s*([dhms])", uptime_str.lower()):
            v = int(val)
            if unit == "d":
                total += v * 86400
            elif unit == "h":
                total += v * 3600
            elif unit == "m":
                total += v * 60
            elif unit == "s":
                total += v
        return total if total else None
    except Exception:
        return None
