"""Contains the Coordinator for updating the IP addresses of your Cloudflare DNS records."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from logging import getLogger
import socket

import pycfdns

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.location import async_detect_location_info
from homeassistant.util.network import is_ipv4_address

from .const import CONF_RECORDS, CONF_ZONES, DEFAULT_UPDATE_INTERVAL

_LOGGER = getLogger(__name__)

type CloudflareConfigEntry = ConfigEntry[CloudflareCoordinator]


class CloudflareCoordinator(DataUpdateCoordinator[None]):
    """Coordinates records updates across one or more Cloudflare zones."""

    config_entry: CloudflareConfigEntry
    client: pycfdns.Client
    zones: list[pycfdns.ZoneModel]

    def __init__(
        self, hass: HomeAssistant, config_entry: CloudflareConfigEntry
    ) -> None:
        """Initialize an coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=config_entry.title,
            update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL),
        )

    def _get_config_value(self, key: str, default=None):
        """Read a value from options first, falling back to data."""
        return self.config_entry.options.get(key) or self.config_entry.data.get(
            key, default
        )

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        self.client = pycfdns.Client(
            api_token=self.config_entry.data[CONF_API_TOKEN],
            client_session=async_get_clientsession(self.hass),
        )

        configured_zone_names: list[str] = self._get_config_value(CONF_ZONES, [])

        try:
            all_zones = await self.client.list_zones()
            self.zones = [
                zone for zone in all_zones if zone["name"] in configured_zone_names
            ]
            if not self.zones:
                raise UpdateFailed(
                    f"None of the configured zones {configured_zone_names} were found"
                )
        except pycfdns.AuthenticationException as e:
            raise ConfigEntryAuthFailed from e
        except pycfdns.ComunicationException as e:
            raise UpdateFailed("Error communicating with API") from e

    async def _async_update_data(self) -> None:
        """Update records across all configured zones."""
        target_records: list[str] = self._get_config_value(CONF_RECORDS, [])

        try:
            location_info = await async_detect_location_info(
                async_get_clientsession(self.hass, family=socket.AF_INET)
            )

            if not location_info or not is_ipv4_address(location_info.ip):
                raise UpdateFailed("Could not get external IPv4 address")

            update_tasks = []
            for zone in self.zones:
                _LOGGER.debug("Checking records in zone %s", zone["name"])
                records = await self.client.list_dns_records(
                    zone_id=zone["id"], type="A"
                )
                _LOGGER.debug("Records in %s: %s", zone["name"], records)

                # Build a map of name -> all IPs currently in this zone
                existing_ips_by_name: dict[str, set[str]] = {}
                for record in records:
                    existing_ips_by_name.setdefault(record["name"], set()).add(
                        record["content"]
                    )

                stale = [
                    record
                    for record in records
                    if record["name"] in target_records
                    and record["content"] != location_info.ip
                    # Skip if another record with the same name already has the target IP
                    # (updating would create a duplicate and Cloudflare will reject it)
                    and location_info.ip
                    not in (
                        existing_ips_by_name[record["name"]] - {record["content"]}
                    )
                ]

                for record in stale:
                    _LOGGER.debug(
                        "Queuing update for record %s in zone %s (current: %s -> new: %s)",
                        record["name"],
                        zone["name"],
                        record["content"],
                        location_info.ip,
                    )
                    update_tasks.append(
                        self.client.update_dns_record(
                            zone_id=zone["id"],
                            record_id=record["id"],
                            record_content=location_info.ip,
                            record_name=record["name"],
                            record_type=record["type"],
                            record_proxied=record["proxied"],
                        )
                    )

            if not update_tasks:
                _LOGGER.debug("All target records are up to date")
                return

            _LOGGER.debug("Submitting %d record update(s)", len(update_tasks))
            await asyncio.gather(*update_tasks)
            _LOGGER.debug("Update complete for all configured zones")

        except pycfdns.AuthenticationException as e:
            raise ConfigEntryAuthFailed from e
        except pycfdns.ComunicationException as e:
            raise UpdateFailed("Error communicating with Cloudflare API") from e
        except UpdateFailed:
            raise
        except Exception as e:
            raise UpdateFailed(f"Unexpected error updating DNS records: {e}") from e
