"""Config and options flow for Public Lands."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import InvalidApiKey, PublicLandsError
from .const import (
    CONF_CAMPGROUNDS,
    CONF_CITY_COUNTY,
    CONF_LOCATION_ENTITY,
    CONF_RIDB_API_KEY,
    CONF_SEARCH_RADIUS,
    DEFAULT_LOCATION_ENTITY,
    DEFAULT_SEARCH_RADIUS,
    DOMAIN,
    MAX_SEARCH_RADIUS,
    MIN_SEARCH_RADIUS,
)
from .extras import async_validate_ridb_key

LOCATION_DOMAINS = ["zone", "device_tracker", "person", "sensor"]


class PublicLandsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up Public Lands. No questions: the defaults work out of the box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return self.async_create_entry(title="Public Lands", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PublicLandsOptionsFlow()


class PublicLandsOptionsFlow(OptionsFlow):
    """Location source and optional features."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._async_validate(user_input)
            if not errors:
                if not user_input.get(CONF_RIDB_API_KEY):
                    user_input.pop(CONF_RIDB_API_KEY, None)
                return self.async_create_entry(title="", data=user_input)

        # Looked up by id so this also works on Home Assistant versions before 2024.11.
        entry = self.hass.config_entries.async_get_entry(self.handler)
        current = dict(entry.options) if entry else {}
        if user_input is not None:
            current.update(user_input)
        return self.async_show_form(
            step_id="init", data_schema=_schema(current), errors=errors
        )

    async def _async_validate(self, user_input: dict[str, Any]) -> dict[str, str]:
        errors: dict[str, str] = {}
        state = self.hass.states.get(user_input[CONF_LOCATION_ENTITY])
        if (
            state is None
            or state.attributes.get(ATTR_LATITUDE) is None
            or state.attributes.get(ATTR_LONGITUDE) is None
        ):
            errors[CONF_LOCATION_ENTITY] = "no_coordinates"

        api_key = (user_input.get(CONF_RIDB_API_KEY) or "").strip()
        user_input[CONF_RIDB_API_KEY] = api_key
        if user_input.get(CONF_CAMPGROUNDS):
            if not api_key:
                errors[CONF_RIDB_API_KEY] = "api_key_required"
            else:
                try:
                    await async_validate_ridb_key(
                        async_get_clientsession(self.hass), api_key
                    )
                except InvalidApiKey:
                    errors[CONF_RIDB_API_KEY] = "invalid_api_key"
                except PublicLandsError:
                    errors[CONF_RIDB_API_KEY] = "cannot_connect"
        return errors


def _schema(current: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_LOCATION_ENTITY,
                default=current.get(CONF_LOCATION_ENTITY) or DEFAULT_LOCATION_ENTITY,
            ): EntitySelector(EntitySelectorConfig(domain=LOCATION_DOMAINS)),
            vol.Required(
                CONF_CITY_COUNTY, default=bool(current.get(CONF_CITY_COUNTY))
            ): BooleanSelector(),
            vol.Required(
                CONF_CAMPGROUNDS, default=bool(current.get(CONF_CAMPGROUNDS))
            ): BooleanSelector(),
            vol.Optional(
                CONF_RIDB_API_KEY,
                description={"suggested_value": current.get(CONF_RIDB_API_KEY, "")},
            ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Required(
                CONF_SEARCH_RADIUS,
                default=current.get(CONF_SEARCH_RADIUS, DEFAULT_SEARCH_RADIUS),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_SEARCH_RADIUS,
                    max=MAX_SEARCH_RADIUS,
                    step=1,
                    unit_of_measurement="mi",
                    mode=NumberSelectorMode.SLIDER,
                )
            ),
        }
    )
