"""Sensors for Zyxel NWA Access Points."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client = hass.data[DOMAIN][entry.entry_id]["client"]
    entities = [
        NWASensor(coordinator, entry, client, key="connected_clients", name="Connected Clients", icon="mdi:devices", unit="clients", state_class=SensorStateClass.MEASUREMENT),
        NWASensor(coordinator, entry, client, key="cpu_usage", name="CPU Usage", icon="mdi:cpu-64-bit", unit="%", state_class=SensorStateClass.MEASUREMENT),
        NWASensor(coordinator, entry, client, key="memory_usage", name="Memory Usage", icon="mdi:memory", unit="%", state_class=SensorStateClass.MEASUREMENT),
        NWASensor(coordinator, entry, client, key="uptime", name="Uptime", icon="mdi:clock-outline", unit="s", device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.TOTAL_INCREASING),
        NWASensor(coordinator, entry, client, key="temperature", name="Temperature", icon="mdi:thermometer", unit="°C", device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),
        NWASensor(coordinator, entry, client, key="firmware", name="Firmware Version", icon="mdi:package-up"),
        NWASensor(coordinator, entry, client, key="model", name="Model", icon="mdi:router-wireless"),
        NWASensor(coordinator, entry, client, key="ssid_count", name="Active SSIDs", icon="mdi:wifi", unit="SSIDs", state_class=SensorStateClass.MEASUREMENT),
    ]
    async_add_entities(entities)

class NWASensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, client, key, name, icon="mdi:router-wireless", unit=None, device_class=None, state_class=None):
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = f"Zyxel NWA {name}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Zyxel {client.model or 'NWA'} ({entry.data['host']})",
            manufacturer="Zyxel",
            model=client.model or "NWA Series",
            sw_version=client.firmware,
            configuration_url=entry.data["host"],
        )

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._key)

    @property
    def available(self):
        return self.coordinator.last_update_success
