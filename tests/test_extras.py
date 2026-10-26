"""Tests for the optional lookups: city and county, rules link, campgrounds."""

from __future__ import annotations

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.public_lands.api import InvalidApiKey
from custom_components.public_lands.const import (
    CENSUS_COUNTIES_URL,
    CENSUS_PLACES_URL,
    NPS_BOUNDARY_URL,
    RIDB_FACILITIES_URL,
    USFS_FOREST_URL,
    USFS_RECREATION_URL,
)
from custom_components.public_lands.extras import (
    async_campgrounds,
    async_city_county,
    async_rules_link,
    short_description,
)
from custom_components.public_lands.rules import (
    blm_office_url,
    forest_campground_url,
    forest_from_legacy_link,
    forest_url,
    fws_refuge_url,
    nps_unit_url,
)

from .conftest import features


def _land(unit: str, manager: str, areas: list[tuple[str, str]] | None = None) -> dict:
    return {
        "unit_name": unit,
        "management_name": manager,
        "areas": [{"unit_name": u, "management_name": m} for u, m in (areas or [(unit, manager)])],
    }


@pytest.mark.parametrize(
    ("name", "url"),
    [
        ("Bishop Field Office", "https://www.blm.gov/office/bishop-field-office"),
        ("Las Cruces District Office", "https://www.blm.gov/office/las-cruces-district-office"),
        ("Alabama Hills National Scenic Area", None),
    ],
)
def test_blm_office_url(name, url) -> None:
    assert blm_office_url(name) == url


@pytest.mark.parametrize(
    ("name", "url"),
    [
        ("Desert National Wildlife Refuge", "https://www.fws.gov/refuge/desert"),
        ("Bosque del Apache National Wildlife Refuge", "https://www.fws.gov/refuge/bosque-del-apache"),
        ("J. N. Ding Darling National Wildlife Refuge", "https://www.fws.gov/refuge/jn-ding-darling"),
        ("St. Marks National Wildlife Refuge", "https://www.fws.gov/refuge/st-marks"),
        ("Adams County Waterfowl Production Area", None),
    ],
)
def test_fws_refuge_url(name, url) -> None:
    assert fws_refuge_url(name) == url


def test_nps_and_forest_urls() -> None:
    assert nps_unit_url("YOSE") == "https://www.nps.gov/yose/index.htm"
    assert forest_url("0504") == "https://www.fs.usda.gov/inyo"
    assert forest_url("9999") is None


async def test_city_and_county(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(CENSUS_PLACES_URL, json=features({"NAME": "San Jose city", "BASENAME": "San Jose"}))
    aioclient_mock.get(CENSUS_COUNTIES_URL, json=features({"NAME": "Santa Clara County", "STATE": "06"}))
    result = await async_city_county(async_get_clientsession(hass), 37.3352, -121.8811)
    assert result == {
        "city": "San Jose",
        "city_full_name": "San Jose city",
        "county": "Santa Clara County",
        "state": "California",
    }


async def test_outside_city_limits(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(CENSUS_PLACES_URL, json=features())
    aioclient_mock.get(CENSUS_COUNTIES_URL, json=features({"NAME": "Inyo County", "STATE": "06"}))
    result = await async_city_county(async_get_clientsession(hass), 36.6, -118.13)
    assert result["city"] == "Unincorporated"
    assert result["county"] == "Inyo County"


async def test_rules_link_blm_uses_field_office(hass: HomeAssistant, aioclient_mock) -> None:
    land = _land(
        "Alabama Hills National Scenic Area",
        "Bureau of Land Management",
        [
            ("Alabama Hills National Scenic Area", "Bureau of Land Management"),
            ("Bishop Field Office", "Bureau of Land Management"),
        ],
    )
    link = await async_rules_link(async_get_clientsession(hass), 36.6, -118.13, land)
    assert link["url"] == "https://www.blm.gov/office/bishop-field-office"
    assert link["name"] == "Bishop Field Office"
    assert link["general_rules_url"] == "https://www.blm.gov/programs/recreation/camping"
    assert aioclient_mock.call_count == 0


async def test_rules_link_nps(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(NPS_BOUNDARY_URL, json=features({"UNIT_CODE": "YOSE", "UNIT_NAME": "Yosemite National Park"}))
    land = _land("Yosemite National Park", "National Park Service")
    link = await async_rules_link(async_get_clientsession(hass), 37.75, -119.59, land)
    assert link["url"] == "https://www.nps.gov/yose/index.htm"


async def test_rules_link_forest(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(USFS_FOREST_URL, json=features({"forestorgcode": "0504", "forestname": "Inyo National Forest"}))
    land = _land("John Muir Wilderness", "Forest Service")
    link = await async_rules_link(async_get_clientsession(hass), 37.3, -118.8, land)
    assert link["url"] == "https://www.fs.usda.gov/inyo"
    assert link["name"] == "Inyo National Forest"


async def test_rules_link_refuge(hass: HomeAssistant) -> None:
    land = _land("Desert National Wildlife Refuge", "U.S. Fish and Wildlife Service")
    link = await async_rules_link(async_get_clientsession(hass), 36.6, -115.5, land)
    assert link["url"] == "https://www.fws.gov/refuge/desert"


async def test_rules_link_other_land_searches_recreation_gov(hass: HomeAssistant) -> None:
    land = _land("Anza-Borrego Desert State Park", "State Park and Recreation")
    link = await async_rules_link(async_get_clientsession(hass), 33.2, -116.4, land)
    assert link["url"] == "https://www.recreation.gov/search?q=Anza-Borrego%20Desert%20State%20Park"


@pytest.mark.parametrize("unit", ["Private Land", "Non-Protected Area"])
async def test_no_rules_link_on_private_land(hass: HomeAssistant, unit) -> None:
    link = await async_rules_link(async_get_clientsession(hass), 35.75, -118.43, _land(unit, "Private"))
    assert link is None


def _facility(fid: str, name: str, lat: float, lon: float, **extra) -> dict:
    return {
        "FacilityID": fid,
        "FacilityName": name,
        "FacilityTypeDescription": "Campground",
        "FacilityLatitude": lat,
        "FacilityLongitude": lon,
        "Reservable": True,
        "StayLimit": "",
        "Enabled": True,
        **extra,
    }


def _fs_site(lat: float, lon: float, status: str) -> dict:
    return {"attributes": {"latitude": str(lat), "longitude": str(lon), "openstatus": status}}


# Near Alabama Hills, as Recreation.gov and the Forest Service reported them (Oct 2026).
NEARBY_FACILITIES = [
    _facility("10004620", "Tuttle Creek Campground", 36.565, -118.127, StayLimit="14 days"),
    _facility(
        "232069",
        "LONE PINE",
        36.5976111,
        -118.1848056,
        FacilityPhone="760-937-6070",
        FacilityDescription=(
            "<h2>Overview</h2><p>Lone Pine Campground is located near the base of "
            "Mt. Whitney.</p>"
        ),
    ),
    _facility(
        "232123", "WHITNEY PORTAL", 36.5898611, -118.2297778, FacilityPhone="760-937-6070"
    ),
    _facility(
        "227765",
        "Ehrenberg Sandbowl",
        36.70,
        -118.05,
        FacilityTypeDescription="Facility",
        Reservable=False,
        ParentRecAreaID="607",
        ACTIVITY=[{"ActivityName": "CAMPING"}, {"ActivityName": "Dispersed Camping"}],
    ),
    _facility("3", "Visitor Center", 36.60, -118.10, FacilityTypeDescription="Facility"),
    _facility("4", "No Coordinates", 0, 0),
    _facility("5", "Far Away Campground", 37.5, -118.13),
]
FOREST_SERVICE_STATUS = {
    "features": [
        _fs_site(36.597069, -118.185447, "open"),  # Lone Pine
        _fs_site(36.588931, -118.232031, "closed"),  # Whitney Portal
    ]
}


async def test_campgrounds(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, json={"RECDATA": NEARBY_FACILITIES, "METADATA": {}})
    aioclient_mock.get(USFS_RECREATION_URL, json=FOREST_SERVICE_STATUS)
    result = await async_campgrounds(async_get_clientsession(hass), "key", 36.6, -118.13, 25)

    # Whitney Portal is closed for the season, so it is hidden.
    assert result["count"] == 3
    assert result["closed_hidden"] == 1
    assert [c["name"] for c in result["campgrounds"]] == [
        "Tuttle Creek Campground",
        "Lone Pine",
        "Ehrenberg Sandbowl",
    ]
    tuttle, lone_pine, dispersed = result["campgrounds"]
    assert tuttle["booking"] == "Reservable"
    assert tuttle["stay_limit"] == "14 days"
    assert tuttle["phone"] is None
    assert tuttle["url"] == "https://www.recreation.gov/camping/campgrounds/10004620"
    assert lone_pine["phone"] == "760-937-6070"
    assert lone_pine["description"] == (
        "Lone Pine Campground is located near the base of Mt. Whitney."
    )
    assert tuttle["description"] is None
    assert lone_pine["directions_url"] == (
        "https://www.google.com/maps/dir/?api=1&destination=36.5976111,-118.1848056"
    )
    assert dispersed["booking"] == "Dispersed"
    assert dispersed["dispersed"] is True
    # Not reservable and not Forest Service: link to the Recreation.gov area page.
    assert dispersed["url"] == "https://www.recreation.gov/gateways/607"
    assert result["attribution"] == "Data source: ridb.recreation.gov"

    # One Recreation.gov request covers campgrounds and dispersed sites.
    ridb_calls = [c for c in aioclient_mock.mock_calls if "ridb" in str(c[1])]
    assert len(ridb_calls) == 1
    _, url, _, headers = ridb_calls[0]
    assert headers == {"apikey": "key"}
    assert url.query["activity"] == "CAMPING,Dispersed Camping"
    assert url.query["full"] == "true"
    assert url.query["radius"] == "25"


async def test_campgrounds_list_nearest_ten(hass: HomeAssistant, aioclient_mock) -> None:
    many = [_facility(str(i), f"Camp {i}", 36.6 + i * 0.01, -118.13) for i in range(15)]
    aioclient_mock.get(RIDB_FACILITIES_URL, json={"RECDATA": many})
    aioclient_mock.get(USFS_RECREATION_URL, json={"features": []})
    result = await async_campgrounds(async_get_clientsession(hass), "key", 36.6, -118.13, 25)
    assert result["count"] == 15
    assert len(result["campgrounds"]) == 10
    assert result["campgrounds"][0]["name"] == "Camp 0"


async def test_campgrounds_shown_if_forest_service_check_fails(
    hass: HomeAssistant, aioclient_mock
) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, json={"RECDATA": NEARBY_FACILITIES})
    aioclient_mock.get(USFS_RECREATION_URL, status=500)
    result = await async_campgrounds(async_get_clientsession(hass), "key", 36.6, -118.13, 25)
    assert result["closed_hidden"] == 0
    assert "Whitney Portal" in [c["name"] for c in result["campgrounds"]]


async def test_campgrounds_bad_key(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(RIDB_FACILITIES_URL, status=401)
    with pytest.raises(InvalidApiKey):
        await async_campgrounds(async_get_clientsession(hass), "bad", 36.6, -118.13, 25)
    assert aioclient_mock.call_count == 1  # no retry on a rejected key


# Descriptions as Recreation.gov sends them (HTML, starting with an "Overview" heading).
TUTTLE_CREEK_HTML = (
    "<h2>Overview</h2><p>$12.00 per site per night. No reservations. Open all year. "
    "Tuttle Creek Campground offers 81 RV/tent sites, with ten pull-through trailer "
    "spaces, maximum recommended RV length is 30 feet.</p>"
)


def test_short_description_cuts_long_text_at_a_word() -> None:
    text = short_description(TUTTLE_CREEK_HTML)
    assert text.startswith("$12.00 per site per night. No reservations. Open all year.")
    assert text.endswith("…")
    assert len(text) <= 161
    assert "<" not in text


def test_short_description_prefers_a_sentence_end() -> None:
    first = "This first sentence is long enough to be worth keeping on its own here."
    rest = " The second sentence keeps going well past the limit " + "and on " * 20
    assert short_description(f"<p>{first}{rest}</p>") == first


def test_short_description_cleans_html() -> None:
    assert short_description("<p>Lake &amp;\n  Creek   views</p>") == "Lake & Creek views"
    assert short_description("OVERVIEW: Quiet sites.") == "Quiet sites."


@pytest.mark.parametrize("empty", [None, "", "<p> </p>"])
def test_short_description_empty(empty) -> None:
    assert short_description(empty) is None


def test_forest_from_legacy_link() -> None:
    url = "https://www.fs.usda.gov/recarea/stanislaus/recarea/?recid=80290"
    assert forest_from_legacy_link(url) == "stanislaus"
    assert forest_from_legacy_link("https://www.recreation.gov/") is None
    assert forest_from_legacy_link("") is None


@pytest.mark.parametrize(
    ("forest", "name", "url"),
    [
        (
            "stanislaus",
            "TeleLi puLaya (Black Oak) Campground",
            "https://www.fs.usda.gov/r05/stanislaus/recreation/teleli-pulaya-black-oak-campground",
        ),
        (
            "stanislaus",
            "Beardsley Dam Campground",
            "https://www.fs.usda.gov/r05/stanislaus/recreation/beardsley-dam-campground",
        ),
        # Forests whose current path differs from their old short name.
        (
            "srnf",
            "Aikens Creek West Campground",
            "https://www.fs.usda.gov/r05/sixrivers/recreation/aikens-creek-west-campground",
        ),
        (
            "bdnf",
            "Lodgepole Campground",
            "https://www.fs.usda.gov/r01/beaverhead-deerlodge/recreation/lodgepole-campground",
        ),
        ("not-a-forest", "Some Campground", None),
    ],
)
def test_forest_campground_url(forest, name, url) -> None:
    assert forest_campground_url(forest, name) == url


async def test_campground_links(hass: HomeAssistant, aioclient_mock) -> None:
    """Reservable: Recreation.gov page. First-come Forest Service: its Forest
    Service page. Anything else: the Recreation.gov area page, or no link."""
    facilities = [
        _facility("10354715", "Meadowview Campground", 36.61, -118.13, ParentRecAreaID="1076"),
        _facility(
            "245552",
            "Beardsley Dam Campground",
            36.62,
            -118.13,
            Reservable=False,
            ParentRecAreaID="1076",
            LINK=[
                {
                    "Title": "Beardsley Dam Campground",
                    "URL": "https://www.fs.usda.gov/recarea/stanislaus/recarea/?recid=15013",
                }
            ],
        ),
        _facility("900", "BLM Camp", 36.63, -118.13, Reservable=False, ParentRecAreaID="607"),
        _facility("901", "No Area Camp", 36.64, -118.13, Reservable=False),
    ]
    aioclient_mock.get(RIDB_FACILITIES_URL, json={"RECDATA": facilities})
    aioclient_mock.get(USFS_RECREATION_URL, json={"features": []})
    result = await async_campgrounds(async_get_clientsession(hass), "key", 36.6, -118.13, 25)
    urls = {c["name"]: c["url"] for c in result["campgrounds"]}
    assert urls == {
        "Meadowview Campground": "https://www.recreation.gov/camping/campgrounds/10354715",
        "Beardsley Dam Campground": (
            "https://www.fs.usda.gov/r05/stanislaus/recreation/beardsley-dam-campground"
        ),
        "BLM Camp": "https://www.recreation.gov/gateways/607",
        "No Area Camp": None,
    }
