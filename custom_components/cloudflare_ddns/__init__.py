"""Update the IP addresses of your Cloudflare DNS records."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_ZONES, DOMAIN, SERVICE_UPDATE_RECORDS
from .coordinator import CloudflareConfigEntry, CloudflareCoordinator

PLATFORMS = ["sensor", "button"]

# Key used in v1 config entries (single zone string from homeassistant.const)
_LEGACY_CONF_ZONE = "zone"


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entries to the current schema version."""
    if config_entry.version < 2:
        new_data = {**config_entry.data}
        if _LEGACY_CONF_ZONE in new_data and CONF_ZONES not in new_data:
            new_data[CONF_ZONES] = [new_data.pop(_LEGACY_CONF_ZONE)]
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: CloudflareConfigEntry) -> bool:
    """Set up Cloudflare DDNS from a config entry."""
    entry.runtime_data = CloudflareCoordinator(hass, entry)
    await entry.runtime_data.async_config_entry_first_refresh()

    # Since we are not using coordinator for data reads, we need to add dummy listener
    entry.async_on_unload(entry.runtime_data.async_add_listener(lambda: None))

    # Reload when the user saves new options via the Configure dialog
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def update_records_service(_: ServiceCall) -> None:
        """Set up service for manual trigger."""
        await entry.runtime_data.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_UPDATE_RECORDS, update_records_service)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: CloudflareConfigEntry
) -> None:
    """Reload the config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: CloudflareConfigEntry) -> bool:
    """Unload Cloudflare DDNS config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
