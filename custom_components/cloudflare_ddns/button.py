"""Button platform for Cloudflare DDNS."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CloudflareConfigEntry, CloudflareCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CloudflareConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cloudflare DDNS button."""
    coordinator: CloudflareCoordinator = entry.runtime_data
    async_add_entities([CloudflareSyncButton(coordinator, entry)])


class CloudflareSyncButton(ButtonEntity):
    """Button to manually trigger a DNS sync."""

    _attr_has_entity_name = True
    _attr_name = "Sync Now"
    _attr_icon = "mdi:sync"

    def __init__(
        self, coordinator: CloudflareCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the button."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_sync_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Cloudflare",
            model="DDNS",
        )

    async def async_press(self) -> None:
        """Trigger a manual DNS sync."""
        await self._coordinator.async_request_refresh()
