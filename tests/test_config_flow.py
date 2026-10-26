"""Tests for the config and options flows."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.public_lands.const import CONF_LOCATION_ENTITY, DOMAIN


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Public Lands"
    assert result["data"] == {}


async def test_only_one_instance(hass: HomeAssistant) -> None:
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    hass.states.async_set("device_tracker.van", "not_home", {"latitude": 37.3, "longitude": -118.8})
    hass.states.async_set("device_tracker.no_gps", "home", {})

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_LOCATION_ENTITY: "device_tracker.no_gps"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_coordinates"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_LOCATION_ENTITY: "device_tracker.van"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_LOCATION_ENTITY: "device_tracker.van"}
