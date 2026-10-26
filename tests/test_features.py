"""Optional features end to end: off by default, sensors appear and disappear."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.public_lands.const import (
    CENSUS_COUNTIES_URL,
    CENSUS_PLACES_URL,
    CONF_CAMPGROUNDS,
    CONF_CITY_COUNTY,
    CONF_LOCATION_ENTITY,
    CONF_RIDB_API_KEY,
    CONF_RULES_LINK,
    CONF_SEARCH_RADIUS,
    DOMAIN,
    RIDB_FACILITIES_URL,
)

from .conftest import ALABAMA_HILLS, BLM_FEE, PADUS_QUERY_URL, features

OPTIONAL_ENTITIES = (
    "sensor.uspl_city",
    "sensor.uspl_county",
    "sensor.uspl_rules_link",
    "sensor.uspl_nearby_campgrounds",
)
ALL_ON = {
    CONF_LOCATION_ENTITY: "zone.home",
    CONF_CITY_COUNTY: True,
    CONF_RULES_LINK: True,
    CONF_CAMPGROUNDS: True,
    CONF_RIDB_API_KEY: "key",
    CONF_SEARCH_RADIUS: 25,
}


async def _setup(hass: HomeAssistant, options: dict | None = None) -> MockConfigEntry:
    hass.states.async_set("zone.home", "0", {"latitude": 36.6, "longitude": -118.13})
    entry = MockConfigEntry(domain=DOMAIN, data={}, options=options or {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _press(hass: HomeAssistant) -> None:
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.refresh_uspl"}, blocking=True
    )
    await hass.async_block_till_done()


def _mock_all(aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features(BLM_FEE, ALABAMA_HILLS))
    aioclient_mock.get(CENSUS_PLACES_URL, json=features())
    aioclient_mock.get(CENSUS_COUNTIES_URL, json=features({"NAME": "Inyo County", "STATE": "06"}))
    aioclient_mock.get(
        RIDB_FACILITIES_URL,
        json={
            "RECDATA": [
                {
                    "FacilityID": "232412",
                    "FacilityName": "TUTTLE CREEK CAMPGROUND",
                    "FacilityTypeDescription": "Campground",
                    "FacilityLatitude": 36.56,
                    "FacilityLongitude": -118.13,
                    "Reservable": False,
                    "Enabled": True,
                }
            ]
        },
    )


async def test_upgrade_adds_no_new_sensors(hass: HomeAssistant, aioclient_mock) -> None:
    """Someone upgrading from v0.2/v0.3.0 sees no new entities and no new requests."""
    _mock_all(aioclient_mock)
    await _setup(hass)
    await _press(hass)
    for entity_id in OPTIONAL_ENTITIES:
        assert hass.states.get(entity_id) is None
    assert aioclient_mock.call_count == 1  # PAD-US only


async def test_all_features_on(hass: HomeAssistant, aioclient_mock) -> None:
    _mock_all(aioclient_mock)
    await _setup(hass, ALL_ON)
    await _press(hass)

    assert hass.states.get("sensor.uspl_city").state == "Unincorporated"
    county = hass.states.get("sensor.uspl_county")
    assert county.state == "Inyo County"
    assert county.attributes["state"] == "California"

    link = hass.states.get("sensor.uspl_rules_link")
    assert link.state == "Bishop Field Office"
    assert link.attributes["url"] == "https://www.blm.gov/office/bishop-field-office"
    assert link.attributes["agency"] == "Bureau of Land Management"
    assert link.attributes["general_rules_url"] == "https://www.blm.gov/programs/recreation/camping"

    camps = hass.states.get("sensor.uspl_nearby_campgrounds")
    assert camps.state == "1"
    assert camps.attributes["nearest"] == "Tuttle Creek Campground"
    assert camps.attributes["attribution"] == "Data source: ridb.recreation.gov"

    # The land sensors are unchanged.
    assert hass.states.get("sensor.uspl_unit_name").state == "Alabama Hills National Scenic Area"


async def test_campgrounds_off_without_key(hass: HomeAssistant, aioclient_mock) -> None:
    _mock_all(aioclient_mock)
    await _setup(hass, {**ALL_ON, CONF_RIDB_API_KEY: ""})
    assert hass.states.get("sensor.uspl_nearby_campgrounds") is None


async def test_optional_failure_does_not_fail_refresh(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features(BLM_FEE, ALABAMA_HILLS))
    aioclient_mock.get(CENSUS_PLACES_URL, status=500)
    aioclient_mock.get(CENSUS_COUNTIES_URL, status=500)
    await _setup(hass, {CONF_CITY_COUNTY: True})
    await _press(hass)
    assert hass.states.get("sensor.uspl_api_status").state == "on"
    assert hass.states.get("sensor.uspl_unit_name").state == "Alabama Hills National Scenic Area"
    assert hass.states.get("sensor.uspl_city").state == "unknown"


async def test_switching_a_feature_off_removes_its_sensors(
    hass: HomeAssistant, aioclient_mock
) -> None:
    _mock_all(aioclient_mock)
    entry = await _setup(hass, {CONF_CITY_COUNTY: True})
    registry = er.async_get(hass)
    assert registry.async_get("sensor.uspl_city") is not None

    hass.config_entries.async_update_entry(entry, options={CONF_CITY_COUNTY: False})
    await hass.async_block_till_done()

    assert registry.async_get("sensor.uspl_city") is None
    assert registry.async_get("sensor.uspl_county") is None
    assert hass.states.get("sensor.uspl_city") is None
    # Core sensors survive the reload.
    assert hass.states.get("sensor.uspl_unit_name") is not None


async def test_lookup_action_includes_features(hass: HomeAssistant, aioclient_mock) -> None:
    _mock_all(aioclient_mock)
    await _setup(hass, {CONF_CITY_COUNTY: True})
    response = await hass.services.async_call(
        DOMAIN,
        "lookup",
        {"latitude": 36.6, "longitude": -118.13},
        blocking=True,
        return_response=True,
    )
    assert response["extras"]["city_county"]["county"] == "Inyo County"
