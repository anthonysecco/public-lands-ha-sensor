"""Tests for the land lookup client."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.public_lands.api import (
    PublicLandsClient,
    PublicLandsError,
    decode_area,
)

from .conftest import (
    ALABAMA_HILLS,
    BLM_FEE,
    DEATH_VALLEY_FEE,
    DEATH_VALLEY_WILDERNESS,
    NEARBY_URL,
    PADUS_QUERY_URL,
    REDWOOD_FEE,
    REDWOOD_MARINE,
    SMA_QUERY_URL,
    features,
    sma,
)


def _client(hass: HomeAssistant) -> PublicLandsClient:
    return PublicLandsClient(async_get_clientsession(hass))


@pytest.mark.parametrize(
    ("codes", "expected"),
    [
        # Codes from the new layer -> wording the old layer returned at the same spot.
        (("FED", "BLM", "NSBV"), ("Federal", "Bureau of Land Management", "National Scenic, Botanical or Volcanic Area")),
        (("FED", "USFS", "WA"), ("Federal", "Forest Service", "Wilderness Area")),
        (("FED", "NPS", "NP"), ("Federal", "National Park Service", "National Park")),
        (("STAT", "SPR", "SREC"), ("State", "State Park and Recreation", "State Recreation Area")),
        (("DIST", "REG", "LP"), ("Regional Agency Special District", "Regional Agency Land", "Local Park")),
        (("LOC", "CITY", "LOTH"), ("Local Government", "City Land", "Local Other or Unknown")),
        (("LOC", "CNTY", "LCA"), ("Local Government", "County Land", "Local Conservation Area")),
    ],
)
def test_decoded_values_match_old_layer(codes, expected) -> None:
    area = decode_area({"Mang_Type": codes[0], "Mang_Name": codes[1], "Des_Tp": codes[2]})
    assert (area["management_type"], area["management_name"], area["designation"]) == expected


def test_unknown_codes_pass_through() -> None:
    area = decode_area({"Mang_Name": "NEWCODE", "Pub_Access": "ZZ"})
    assert area["management_name"] == "NEWCODE"
    assert area["public_access"] == "Unknown"
    assert area["unit_name"] == "Unknown"


async def test_designation_wins_and_shows_underlying_land(hass, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features(BLM_FEE, ALABAMA_HILLS))
    result = await _client(hass).async_lookup(36.600049, -118.130049)

    assert result["unit_name"] == "Alabama Hills National Scenic Area"
    assert result["public_access"] == "Restricted Access"
    assert result["management_type"] == "Federal"
    assert result["management_name"] == "Bureau of Land Management"
    assert result["designation"] == "National Scenic, Botanical or Volcanic Area"
    assert result["underlying_land"] == "Bishop Field Office"
    assert result["source"] == "PAD-US"
    assert [a["unit_name"] for a in result["areas"]] == [
        "Alabama Hills National Scenic Area",
        "Bishop Field Office",
    ]
    assert (result["latitude"], result["longitude"]) == (36.6, -118.13)
    # Only PAD-US is called when it has an answer.
    assert aioclient_mock.call_count == 1
    assert "geometry=-118.13,36.6" in str(aioclient_mock.mock_calls[0][1]).replace("%2C", ",")


async def test_fee_wins_over_marine(hass, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features(REDWOOD_MARINE, REDWOOD_FEE))
    result = await _client(hass).async_lookup(41.3, -124.04)
    assert result["designation"] == "National Park"
    assert result["underlying_land"] is None


@pytest.mark.parametrize(("code", "manager"), [("PVT", "Private"), ("UND", "Undetermined")])
async def test_private_land(hass, aioclient_mock, code, manager) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features())
    aioclient_mock.get(SMA_QUERY_URL, json=sma(code))
    result = await _client(hass).async_lookup(35.75, -118.43)

    assert result["unit_name"] == "Private Land"
    assert result["public_access"] == "Private Land"
    assert result["management_type"] == "Private"
    assert result["surface_manager"] == manager
    assert result["source"] == "BLM Surface Management"


async def test_gap_filled_by_nearby_area_from_same_manager(hass, aioclient_mock) -> None:
    # Badwater: PAD-US has a gap, BLM says National Park Service.
    aioclient_mock.get(
        NEARBY_URL, json=features(BLM_FEE, DEATH_VALLEY_FEE, DEATH_VALLEY_WILDERNESS)
    )
    aioclient_mock.get(PADUS_QUERY_URL, json=features())
    aioclient_mock.get(SMA_QUERY_URL, json=sma("NPS"))
    result = await _client(hass).async_lookup(36.23, -116.77)

    assert result["unit_name"] == "Death Valley Wilderness Area"
    assert result["underlying_land"] == "Death Valley National Park"
    assert result["source"] == "PAD-US (nearby)"
    # The BLM record nearby is ignored because BLM's map says NPS manages this spot.
    assert all(a["management_name"] == "National Park Service" for a in result["areas"])


async def test_gap_without_nearby_match_uses_blm_answer(hass, aioclient_mock) -> None:
    aioclient_mock.get(NEARBY_URL, json=features(BLM_FEE))
    aioclient_mock.get(PADUS_QUERY_URL, json=features())
    aioclient_mock.get(SMA_QUERY_URL, json=sma("NPS"))
    result = await _client(hass).async_lookup(36.46, -116.87)

    assert result["unit_name"] == "National Park Service"
    assert result["management_name"] == "National Park Service"
    assert result["management_type"] == "Federal"
    assert result["designation"] == "Unknown"
    assert result["source"] == "BLM Surface Management"


async def test_blm_failure_falls_back_to_non_protected(hass, aioclient_mock) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, json=features())
    aioclient_mock.get(SMA_QUERY_URL, status=500)
    result = await _client(hass).async_lookup(0.0, -140.0)
    assert result["unit_name"] == "Non-Protected Area"
    assert result["public_access"] == "Unknown"


async def test_service_error_in_http_200_is_a_failure(hass, aioclient_mock) -> None:
    aioclient_mock.get(
        PADUS_QUERY_URL,
        json={"error": {"code": 400, "message": "Cannot perform query"}},
    )
    with pytest.raises(PublicLandsError, match="Cannot perform query"):
        await _client(hass).async_lookup(36.6, -118.13)
    assert aioclient_mock.call_count == 2  # retried once


@pytest.mark.parametrize(
    "kwargs",
    [{"status": 503}, {"text": "<html>not json</html>"}, {"exc": TimeoutError()}],
)
async def test_transport_failures_raise(hass, aioclient_mock, kwargs) -> None:
    aioclient_mock.get(PADUS_QUERY_URL, **kwargs)
    with pytest.raises(PublicLandsError):
        await _client(hass).async_lookup(36.6, -118.13)
