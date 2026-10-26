"""Tests for the config and options flows."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.public_lands.const import (
    CONF_CAMPGROUNDS,
    CONF_CITY_COUNTY,
    CONF_LOCATION_ENTITY,
    CONF_RIDB_API_KEY,
    CONF_RULES_LINK,
    CONF_SEARCH_RADIUS,
    DOMAIN,
    RIDB_FACILITIES_URL,
)


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


async def _options_form(hass: HomeAssistant) -> tuple[MockConfigEntry, dict]:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    hass.states.async_set("zone.home", "0", {"latitude": 36.6, "longitude": -118.13})
    hass.states.async_set("device_tracker.van", "not_home", {"latitude": 37.3, "longitude": -118.8})
    hass.states.async_set("device_tracker.no_gps", "home", {})
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    return entry, result


async def test_options_defaults_are_off(hass: HomeAssistant) -> None:
    entry, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_LOCATION_ENTITY: "zone.home",
        CONF_CITY_COUNTY: False,
        CONF_RULES_LINK: False,
        CONF_CAMPGROUNDS: False,
        CONF_SEARCH_RADIUS: 25,
    }


async def test_options_location_entity(hass: HomeAssistant) -> None:
    entry, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_LOCATION_ENTITY: "device_tracker.no_gps"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_LOCATION_ENTITY: "no_coordinates"}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_LOCATION_ENTITY: "device_tracker.van"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_LOCATION_ENTITY] == "device_tracker.van"


async def test_campgrounds_need_a_key(hass: HomeAssistant) -> None:
    _, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_CAMPGROUNDS: True}
    )
    assert result["errors"] == {CONF_RIDB_API_KEY: "api_key_required"}


async def test_campgrounds_invalid_key(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, status=401)
    _, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_CAMPGROUNDS: True, CONF_RIDB_API_KEY: "bad"}
    )
    assert result["errors"] == {CONF_RIDB_API_KEY: "invalid_api_key"}


async def test_campgrounds_service_down(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, status=503)
    _, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_CAMPGROUNDS: True, CONF_RIDB_API_KEY: "key"}
    )
    assert result["errors"] == {CONF_RIDB_API_KEY: "cannot_connect"}


async def test_campgrounds_valid_key(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, json={"RECDATA": [], "METADATA": {}})
    entry, result = await _options_form(hass)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_CAMPGROUNDS: True, CONF_RIDB_API_KEY: " good-key ", CONF_SEARCH_RADIUS: 10},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_RIDB_API_KEY] == "good-key"
    assert entry.options[CONF_SEARCH_RADIUS] == 10
    headers = aioclient_mock.mock_calls[-1][3]
    assert headers == {"apikey": "good-key"}
