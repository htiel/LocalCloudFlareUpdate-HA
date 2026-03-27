"""Config flow for Cloudflare DDNS integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import pycfdns
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_RECORDS,
    CONF_SCAN_INTERVAL,
    CONF_ZONES,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    WARN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): vol.All(str, str.strip, vol.Length(min=1)),
    }
)


def _options_init_schema(
    zones: list[pycfdns.ZoneModel] | None = None,
    current_zones: list[str] | None = None,
    current_interval: int = DEFAULT_UPDATE_INTERVAL,
) -> vol.Schema:
    """Combined schema for options init step: zones + scan interval."""
    zones_dict: dict[str, str] = {}
    if zones is not None:
        zones_dict = {zone["name"]: zone["name"] for zone in zones}
    return vol.Schema(
        {
            vol.Required(
                CONF_ZONES,
                default=current_zones or [],
            ): cv.multi_select(zones_dict),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=current_interval,
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL)),
        }
    )


def _zones_schema(
    zones: list[pycfdns.ZoneModel] | None = None,
    current_zones: list[str] | None = None,
) -> vol.Schema:
    """Zone multi-selection schema."""
    zones_dict: dict[str, str] = {}
    if zones is not None:
        zones_dict = {zone["name"]: zone["name"] for zone in zones}
    return vol.Schema(
        {
            vol.Required(
                CONF_ZONES,
                default=current_zones or [],
            ): cv.multi_select(zones_dict)
        }
    )


def _records_schema(
    records: list[pycfdns.RecordModel] | None = None,
    current_records: list[str] | None = None,
) -> vol.Schema:
    """Zone records selection schema."""
    records_dict: dict[str, str] = {}
    if records:
        records_dict = {record["name"]: record["name"] for record in records}
    return vol.Schema(
        {
            vol.Required(
                CONF_RECORDS,
                default=current_records or [],
            ): cv.multi_select(records_dict)
        }
    )


async def _fetch_zones(
    hass: HomeAssistant, api_token: str
) -> list[pycfdns.ZoneModel]:
    """Fetch all zones available to the given API token."""
    client = pycfdns.Client(
        api_token=api_token,
        client_session=async_get_clientsession(hass),
    )
    return await client.list_zones()


async def _fetch_records_for_zones(
    hass: HomeAssistant,
    api_token: str,
    zone_names: list[str],
) -> list[pycfdns.RecordModel]:
    """Fetch all A records across the specified zones."""
    client = pycfdns.Client(
        api_token=api_token,
        client_session=async_get_clientsession(hass),
    )
    all_zones = await client.list_zones()
    all_records: list[pycfdns.RecordModel] = []
    for zone in all_zones:
        if zone["name"] in zone_names:
            records = await client.list_dns_records(zone_id=zone["id"], type="A")
            all_records.extend(records)
    return all_records


class CloudflareConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloudflare DDNS."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the Cloudflare DDNS config flow."""
        self.cloudflare_config: dict[str, Any] = {}
        self.zones: list[pycfdns.ZoneModel] | None = None
        self.records: list[pycfdns.RecordModel] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> CloudflareOptionsFlowHandler:
        """Return the options flow handler."""
        return CloudflareOptionsFlowHandler()

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle initiation of re-authentication with Cloudflare."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication with Cloudflare."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await _fetch_zones(self.hass, user_input[CONF_API_TOKEN])
            except pycfdns.ComunicationException:
                errors["base"] = "cannot_connect"
            except pycfdns.AuthenticationException:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                reauth_entry = self._get_reauth_entry()
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data={
                        **reauth_entry.data,
                        CONF_API_TOKEN: user_input[CONF_API_TOKEN],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self.zones = await _fetch_zones(self.hass, user_input[CONF_API_TOKEN])
            except pycfdns.ComunicationException:
                errors["base"] = "cannot_connect"
            except pycfdns.AuthenticationException:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self.cloudflare_config.update(user_input)
                return await self.async_step_zones()

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle picking the zones to update."""
        errors: dict[str, str] = {}

        if user_input is not None:
            selected_zones: list[str] = user_input[CONF_ZONES]
            if not selected_zones:
                errors[CONF_ZONES] = "no_zones_selected"
            else:
                try:
                    self.records = await _fetch_records_for_zones(
                        self.hass,
                        self.cloudflare_config[CONF_API_TOKEN],
                        selected_zones,
                    )
                except pycfdns.ComunicationException:
                    errors["base"] = "cannot_connect"
                except pycfdns.AuthenticationException:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    self.cloudflare_config.update(user_input)
                    return await self.async_step_records()

        return self.async_show_form(
            step_id="zones",
            data_schema=_zones_schema(self.zones),
            errors=errors,
        )

    async def async_step_records(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle picking the DNS records to update."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input[CONF_RECORDS]:
                errors[CONF_RECORDS] = "no_records_selected"
            else:
                self.cloudflare_config.update(user_input)
                title = ", ".join(self.cloudflare_config[CONF_ZONES])
                return self.async_create_entry(title=title, data=self.cloudflare_config)

        return self.async_show_form(
            step_id="records",
            data_schema=_records_schema(self.records),
            errors=errors,
        )


class CloudflareOptionsFlowHandler(OptionsFlow):
    """Handle Cloudflare DDNS options — update zones and records without re-adding."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self.options: dict[str, Any] = {}
        self.available_zones: list[pycfdns.ZoneModel] | None = None
        self.available_records: list[pycfdns.RecordModel] | None = None
        self._interval_warning_acknowledged: bool = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show zone multi-select and scan interval, pre-populated with current values."""
        errors: dict[str, str] = {}

        current_zones: list[str] = (
            self.config_entry.options.get(CONF_ZONES)
            or self.config_entry.data.get(CONF_ZONES, [])
        )
        current_interval: int = int(
            self.config_entry.options.get(CONF_SCAN_INTERVAL)
            or self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )

        if user_input is not None:
            selected_zones: list[str] = user_input[CONF_ZONES]
            interval: int = user_input[CONF_SCAN_INTERVAL]

            if not selected_zones:
                errors[CONF_ZONES] = "no_zones_selected"
            elif interval < MIN_UPDATE_INTERVAL:
                errors[CONF_SCAN_INTERVAL] = "interval_too_low"
            elif interval < WARN_UPDATE_INTERVAL and not self._interval_warning_acknowledged:
                # Show a warning on first submit; allow on second submit
                errors[CONF_SCAN_INTERVAL] = "interval_low_warning"
                self._interval_warning_acknowledged = True
            else:
                self._interval_warning_acknowledged = False
                try:
                    self.available_records = await _fetch_records_for_zones(
                        self.hass,
                        self.config_entry.data[CONF_API_TOKEN],
                        selected_zones,
                    )
                except pycfdns.ComunicationException:
                    errors["base"] = "cannot_connect"
                except pycfdns.AuthenticationException:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    self.options.update(user_input)
                    return await self.async_step_records()

        if self.available_zones is None:
            try:
                self.available_zones = await _fetch_zones(
                    self.hass, self.config_entry.data[CONF_API_TOKEN]
                )
            except Exception:
                _LOGGER.exception("Failed to fetch zones for options flow")
                return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="init",
            data_schema=_options_init_schema(
                self.available_zones, current_zones, current_interval
            ),
            errors=errors,
        )

    async def async_step_records(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show record multi-select, pre-populated with the current selection."""
        errors: dict[str, str] = {}

        current_records: list[str] = (
            self.config_entry.options.get(CONF_RECORDS)
            or self.config_entry.data.get(CONF_RECORDS, [])
        )

        if user_input is not None:
            if not user_input[CONF_RECORDS]:
                errors[CONF_RECORDS] = "no_records_selected"
            else:
                self.options.update(user_input)
                return self.async_create_entry(data=self.options)

        return self.async_show_form(
            step_id="records",
            data_schema=_records_schema(self.available_records, current_records),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
