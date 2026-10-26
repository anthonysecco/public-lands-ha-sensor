"""Tests for setup, sensors, the refresh button and upgrades from v0.2.x."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.public_lands.const import CONF_LOCATION_ENTITY, DOMAIN

from .conftest import (
    ALABAMA_HILLS,
    BLM_FEE,
    PADUS_QUERY_URL,
    SMA_QUERY_URL,
    features,
    sma,
)

# Entity IDs created by v0.2.x. They must not change.
ENTITY_IDS = {
    "uspl_Unit_Nm": "sensor.uspl_unit_name",
    "uspl_Pub_Access": "sensor.uspl_public_access",
    "uspl_MngTp_Desc": "sensor.uspl_management_type",
    "uspl_MngNm_Desc": "sensor.uspl_management_name",
    "uspl_DesTp_Desc": "sensor.uspl_designation",
    "uspl_last_success": "sensor.uspl_last_successful_refresh",
    "uspl_api_status": "sensor.uspl_api_status",
    "refresh_uspl": "button.refresh_uspl",
}


async def _setup(hass: HomeAssistant, options: dict | None = None) -> MockConfigEntry:
    hass.states.async_set("zone.home", "0", {"latitude": 36.6, "longitude": -118.13})
    entry = MockConfigEntry(domain=DOMAIN, title="Public Lands", data={}, options=options or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _press(hass: HomeAssistant) -> None:
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.refresh_uspl"}, blocking=True
    )
    await hass.async_block_till_done()


async def test_entity_ids_unchanged(hass: HomeAssistant) -> None:
    await _setup(hass)
    registry = er.async_get(hass)
    for unique_id, entity_id in ENTITY_IDS.items():
        domain = entity_id.split(".")[0]
        assert registry.async_get_entity_id(domain, DOMAIN, unique_id) == entity_id
        assert hass.states.get(entity_id) is not None, entity_id


async def test_upgrade_keeps_renamed_entities(hass: HomeAssistant) -> None:
    """Entities a user renamed under v0.2.x keep their IDs after upgrading."""
    entry = MockConfigEntry(domain=DOMAIN, title="Public Lands", data={})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "sensor", DOMAIN, "uspl_Unit_Nm", config_entry=entry, suggested_object_id="van_land"
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert registry.async_get_entity_id("sensor", DOMAIN, "uspl_Unit_Nm") == "sensor.van_land"
    assert hass.states.get("sensor.van_land") is not None
    assert hass.states.get("sensor.uspl_unit_name") is None


async def test_no_data_until_pressed(hass: HomeAssistant, aioclient_mock) -> None:
    await _setup(hass)
    assert hass.states.get("sensor.uspl_unit_name").state == "unknown"
    assert hass.states.get("sensor.uspl_api_status").state == "off"
    assert hass.states.get("sensor.uspl_last_successful_refresh").state == "unknown"
    assert aioclient_mock.call_count == 0


async def test_press_updates_sensors(hass: HomeAssistant, mock_alabama_hills) -> None:
    await _setup(hass)
    await _press(hass)

    unit = hass.states.get("sensor.uspl_unit_name")
    assert unit.state == "Alabama Hills National Scenic Area"
    assert unit.attributes["underlying_land"] == "Bishop Field Office"
    assert unit.attributes["source"] == "PAD-US"
    assert unit.attributes["location_entity"] == "zone.home"
    assert hass.states.get("sensor.uspl_public_access").state == "Restricted Access"
    assert hass.states.get("sensor.uspl_management_type").state == "Federal"
    assert hass.states.get("sensor.uspl_management_name").state == "Bureau of Land Management"
    assert (
        hass.states.get("sensor.uspl_designation").state
        == "National Scenic, Botanical or Volcanic Area"
    )
    assert hass.states.get("sensor.uspl_api_status").state == "on"
    assert hass.states.get("sensor.uspl_last_successful_refresh").state not in (
        "unknown",
        "unavailable",
    )


async def test_private_land(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features())
    aioclient_mock.get(SMA_QUERY_URL, json=sma("PVT"))
    await _setup(hass)
    await _press(hass)
    assert hass.states.get("sensor.uspl_unit_name").state == "Private Land"
    assert hass.states.get("sensor.uspl_api_status").state == "on"


async def test_failure_keeps_last_values(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features(BLM_FEE, ALABAMA_HILLS))
    await _setup(hass)
    await _press(hass)

    aioclient_mock.clear_requests()
    aioclient_mock.get(PADUS_QUERY_URL, json={"error": {"code": 500, "message": "down"}})
    await _press(hass)

    assert hass.states.get("sensor.uspl_api_status").state == "off"
    unit = hass.states.get("sensor.uspl_unit_name")
    assert unit.state == "Alabama Hills National Scenic Area"


async def test_values_survive_reload(hass: HomeAssistant, mock_alabama_hills) -> None:
    entry = await _setup(hass)
    await _press(hass)
    calls = mock_alabama_hills.call_count

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.uspl_unit_name").state == "Alabama Hills National Scenic Area"
    assert hass.states.get("sensor.uspl_api_status").state == "on"
    assert hass.states.get("sensor.uspl_last_successful_refresh").state not in (
        "unknown",
        "unavailable",
    )
    assert mock_alabama_hills.call_count == calls  # restored, not refetched

    # The button still works after a reload.
    await _press(hass)
    assert mock_alabama_hills.call_count == calls + 1


async def test_unload(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_custom_location_entity(hass: HomeAssistant, mock_alabama_hills) -> None:
    hass.states.async_set(
        "device_tracker.van", "not_home", {"latitude": 37.3, "longitude": -118.8}
    )
    await _setup(hass, {CONF_LOCATION_ENTITY: "device_tracker.van"})
    await _press(hass)
    url = str(mock_alabama_hills.mock_calls[-1][1]).replace("%2C", ",")
    assert "geometry=-118.8,37.3" in url
    assert (
        hass.states.get("sensor.uspl_unit_name").attributes["location_entity"]
        == "device_tracker.van"
    )


async def test_location_entity_without_coordinates(hass: HomeAssistant, aioclient_mock) -> None:
    hass.states.async_set("device_tracker.van", "home", {})
    await _setup(hass, {CONF_LOCATION_ENTITY: "device_tracker.van"})
    await _press(hass)
    assert hass.states.get("sensor.uspl_api_status").state == "off"
    assert aioclient_mock.call_count == 0


async def test_zone_home_missing_uses_configured_coordinates(
    hass: HomeAssistant, mock_alabama_hills
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, title="Public Lands", data={})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_remove("zone.home")
    await _press(hass)
    lat = round(hass.config.latitude, 4)
    lon = round(hass.config.longitude, 4)
    url = str(mock_alabama_hills.mock_calls[-1][1]).replace("%2C", ",")
    assert f"geometry={lon},{lat}" in url
