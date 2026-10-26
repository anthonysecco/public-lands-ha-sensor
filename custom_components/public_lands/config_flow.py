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
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import CONF_LOCATION_ENTITY, DEFAULT_LOCATION_ENTITY, DOMAIN

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
    """Choose which entity provides the location."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            state = self.hass.states.get(user_input[CONF_LOCATION_ENTITY])
            if (
                state is None
                or state.attributes.get(ATTR_LATITUDE) is None
                or state.attributes.get(ATTR_LONGITUDE) is None
            ):
                errors["base"] = "no_coordinates"
            else:
                return self.async_create_entry(title="", data=user_input)

        # Looked up by id so this also works on Home Assistant versions before 2024.11.
        entry = self.hass.config_entries.async_get_entry(self.handler)
        current = (
            entry.options.get(CONF_LOCATION_ENTITY) if entry else None
        ) or DEFAULT_LOCATION_ENTITY
        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATION_ENTITY, default=current): EntitySelector(
                    EntitySelectorConfig(domain=LOCATION_DOMAINS)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
