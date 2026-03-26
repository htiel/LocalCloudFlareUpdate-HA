"""Sensor platform for Cloudflare DDNS."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CloudflareConfigEntry, CloudflareCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudflareConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare DDNS sensors."""
    coordinator: CloudflareCoordinator = entry.runtime_data
    async_add_entities(
        [
            CloudflareLastSyncSensor(coordinator, entry),
            CloudflareSyncStatusSensor(coordinator, entry),
        ]
    )


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return shared device info for all Cloudflare DDNS entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Cloudflare",
        model="DDNS",
        entry_type=DeviceEntryType.SERVICE,
    )


class CloudflareLastSyncSensor(
    CoordinatorEntity[CloudflareCoordinator], SensorEntity
):
    """Sensor showing the timestamp of the last sync attempt."""

    _attr_has_entity_name = True
    _attr_name = "Last Sync"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, coordinator: CloudflareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_sync"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> datetime | None:
        """Return the last sync time."""
        return self.coordinator.last_sync_time


class CloudflareSyncStatusSensor(
    CoordinatorEntity[CloudflareCoordinator], SensorEntity
):
    """Sensor showing the result of the last sync."""

    _attr_has_entity_name = True
    _attr_name = "Sync Status"
    _attr_icon = "mdi:dns"

    def __init__(
        self, coordinator: CloudflareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_sync_status"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> str:
        """Return the sync status string."""
        if self.coordinator.last_sync_time is None:
            return "Pending"
        if not self.coordinator.last_update_success:
            return "Failed"
        count = self.coordinator.last_sync_records_updated
        if count == 0:
            return "Up to date"
        return f"{count} record{'s' if count != 1 else ''} updated"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "records_updated": self.coordinator.last_sync_records_updated,
        }
