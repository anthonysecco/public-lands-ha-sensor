"""Tests for the public_lands.lookup action."""

from __future__ import annotations

import pytest
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.public_lands.const import DOMAIN

from .conftest import PADUS_QUERY_URL


async def _setup(hass: HomeAssistant) -> MockConfigEntry:
    hass.states.async_set("zone.home", "0", {"latitude": 36.6, "longitude": -118.13})
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _lookup(hass: HomeAssistant, data: dict) -> dict:
    return await hass.services.async_call(
        DOMAIN, "lookup", data, blocking=True, return_response=True
    )


async def test_lookup_coordinates_does_not_touch_sensors(
    hass: HomeAssistant, mock_alabama_hills
) -> None:
    await _setup(hass)
    response = await _lookup(hass, {"latitude": 37.3, "longitude": -118.8})

    assert response["unit_name"] == "Alabama Hills National Scenic Area"
    assert response["underlying_land"] == "Bishop Field Office"
    url = str(mock_alabama_hills.mock_calls[-1][1]).replace("%2C", ",")
    assert "geometry=-118.8,37.3" in url
    assert hass.states.get("sensor.uspl_unit_name").state == "unknown"


async def test_lookup_defaults_to_current_location(hass: HomeAssistant, mock_alabama_hills) -> None:
    await _setup(hass)
    await _lookup(hass, {})
    url = str(mock_alabama_hills.mock_calls[-1][1]).replace("%2C", ",")
    assert "geometry=-118.13,36.6" in url


async def test_lookup_needs_both_coordinates(hass: HomeAssistant) -> None:
    await _setup(hass)
    with pytest.raises((vol.Invalid, ServiceValidationError)):
        await _lookup(hass, {"latitude": 37.3})


async def test_lookup_failure(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, status=500)
    await _setup(hass)
    with pytest.raises(HomeAssistantError):
        await _lookup(hass, {"latitude": 37.3, "longitude": -118.8})


async def test_lookup_when_not_loaded(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    with pytest.raises(ServiceValidationError):
        await _lookup(hass, {"latitude": 37.3, "longitude": -118.8})
