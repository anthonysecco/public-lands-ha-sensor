"""Optional lookups: city and county, rules link, nearby campgrounds."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

import aiohttp

from .api import PublicLandsError, arcgis_point_query, get_json
from .const import (
    CENSUS_COUNTIES_URL,
    CENSUS_PLACES_URL,
    FS_MATCH_DISTANCE_MI,
    MAX_CAMPGROUNDS_LISTED,
    NON_PROTECTED_AREA,
    NPS_BOUNDARY_URL,
    PRIVATE_LAND,
    RIDB_ATTRIBUTION,
    RIDB_FACILITIES_URL,
    UNKNOWN,
    USFS_FOREST_URL,
    USFS_RECREATION_URL,
)
from .rules import (
    BLM_CAMPING_URL,
    blm_office_url,
    forest_url,
    fws_refuge_url,
    nps_unit_url,
    recreation_gov_search_url,
)

UNINCORPORATED = "Unincorporated"

STATE_FIPS: dict[str, str] = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa", "20": "Kansas",
    "21": "Kentucky", "22": "Louisiana", "23": "Maine", "24": "Maryland",
    "25": "Massachusetts", "26": "Michigan", "27": "Minnesota", "28": "Mississippi",
    "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
    "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
    "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina",
    "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah",
    "50": "Vermont", "51": "Virginia", "53": "Washington", "54": "West Virginia",
    "55": "Wisconsin", "56": "Wyoming", "60": "American Samoa", "66": "Guam",
    "69": "Northern Mariana Islands", "72": "Puerto Rico", "78": "U.S. Virgin Islands",
}  # fmt: skip


def _first_attrs(features: list[dict[str, Any]]) -> dict[str, Any] | None:
    return (features[0].get("attributes") or {}) if features else None


async def async_city_county(
    session: aiohttp.ClientSession, lat: float, lon: float
) -> dict[str, Any]:
    """City limits (incorporated place) and county from the Census Bureau."""
    place = _first_attrs(
        await arcgis_point_query(session, CENSUS_PLACES_URL, lat, lon, "NAME,BASENAME")
    )
    county = _first_attrs(
        await arcgis_point_query(session, CENSUS_COUNTIES_URL, lat, lon, "NAME,STATE")
    )
    return {
        "city": (place.get("BASENAME") or place.get("NAME")) if place else UNINCORPORATED,
        "city_full_name": place.get("NAME") if place else None,
        "county": county.get("NAME") if county else UNKNOWN,
        "state": STATE_FIPS.get(str(county.get("STATE"))) if county else None,
    }


async def async_rules_link(
    session: aiohttp.ClientSession, lat: float, lon: float, land: dict[str, Any]
) -> dict[str, Any] | None:
    """Link to the managing unit's own page. None on private or unknown land."""
    unit = land.get("unit_name")
    if unit in (PRIVATE_LAND, NON_PROTECTED_AREA, None):
        return None
    manager = land.get("management_name") or UNKNOWN
    areas = land.get("areas") or []
    link: dict[str, Any] = {"name": unit, "agency": manager, "general_rules_url": None}

    if manager == "Bureau of Land Management":
        office = next(
            (
                a["unit_name"]
                for a in areas
                if a.get("management_name") == manager and blm_office_url(a["unit_name"])
            ),
            None,
        )
        link["general_rules_url"] = BLM_CAMPING_URL
        if office:
            link.update(name=office, url=blm_office_url(office))
        else:
            link["url"] = BLM_CAMPING_URL
        return link

    if manager == "National Park Service":
        park = _first_attrs(
            await arcgis_point_query(
                session, NPS_BOUNDARY_URL, lat, lon, "UNIT_CODE,UNIT_NAME"
            )
        )
        if park and park.get("UNIT_CODE"):
            link.update(name=park.get("UNIT_NAME") or unit, url=nps_unit_url(park["UNIT_CODE"]))
            return link

    elif manager == "Forest Service":
        forest = _first_attrs(
            await arcgis_point_query(
                session, USFS_FOREST_URL, lat, lon, "forestorgcode,forestname"
            )
        )
        if forest and (url := forest_url(str(forest.get("forestorgcode")))):
            link.update(name=forest.get("forestname") or unit, url=url)
            return link

    elif manager == "U.S. Fish and Wildlife Service":
        refuge = next(
            (a["unit_name"] for a in areas if fws_refuge_url(a["unit_name"])), None
        )
        if refuge:
            link.update(name=refuge, url=fws_refuge_url(refuge))
            return link

    link["url"] = recreation_gov_search_url(unit)
    return link


def _miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 3958.8 * 2 * asin(sqrt(a))


async def async_validate_ridb_key(session: aiohttp.ClientSession, api_key: str) -> None:
    """Raise InvalidApiKey or PublicLandsError if the key does not work."""
    await get_json(session, RIDB_FACILITIES_URL, {"limit": "1"}, {"apikey": api_key})


async def _forest_service_status(
    session: aiohttp.ClientSession, lat: float, lon: float, radius_mi: float
) -> list[tuple[float, float, str]]:
    """Open/closed status of Forest Service campgrounds near a point.

    Recreation.gov has no open/closed field, but the Forest Service publishes
    one for its own campgrounds. Returns (lat, lon, status) tuples; empty if
    the lookup fails, so campgrounds are then shown rather than hidden.
    """
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "distance": str(radius_mi + 2),
        "units": "esriSRUnit_StatuteMile",
        "where": "markeractivity LIKE '%Camping%'",
        "outFields": "openstatus,latitude,longitude",
        "returnGeometry": "false",
        "f": "json",
    }
    try:
        data = await get_json(session, USFS_RECREATION_URL, params)
    except PublicLandsError:
        return []
    sites: list[tuple[float, float, str]] = []
    for feature in data.get("features") or []:
        attrs = feature.get("attributes") or {}
        try:
            sites.append(
                (
                    float(attrs["latitude"]),
                    float(attrs["longitude"]),
                    str(attrs.get("openstatus") or "").lower(),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return sites


def _is_closed(lat: float, lon: float, fs_sites: list[tuple[float, float, str]]) -> bool:
    """Closed if the nearest Forest Service campground (within 1.5 mi) says so."""
    nearest = min(
        ((_miles(lat, lon, s_lat, s_lon), status) for s_lat, s_lon, status in fs_sites),
        default=None,
    )
    return bool(nearest and nearest[0] <= FS_MATCH_DISTANCE_MI and nearest[1] == "closed")


async def async_campgrounds(
    session: aiohttp.ClientSession,
    api_key: str,
    lat: float,
    lon: float,
    radius_mi: float,
) -> dict[str, Any]:
    """Recreation.gov campgrounds and dispersed sites within radius_mi.

    One Recreation.gov request plus one free Forest Service status check.
    Campgrounds the Forest Service reports closed are left out. The nearest
    ten are listed; the count covers all of them.
    """
    data = await get_json(
        session,
        RIDB_FACILITIES_URL,
        {
            "latitude": str(lat),
            "longitude": str(lon),
            "radius": str(radius_mi),
            "activity": "CAMPING,Dispersed Camping",
            "full": "true",
            "limit": "50",
        },
        {"apikey": api_key},
    )
    fs_sites = await _forest_service_status(session, lat, lon, radius_mi)

    camps: list[dict[str, Any]] = []
    closed = 0
    for fac in data.get("RECDATA") or []:
        activities = {
            str(a.get("ActivityName", "")).lower() for a in fac.get("ACTIVITY") or []
        }
        dispersed = "dispersed camping" in activities
        is_campground = "campground" in str(fac.get("FacilityTypeDescription", "")).lower()
        if not (is_campground or dispersed) or fac.get("Enabled") is False:
            continue
        flat, flon = fac.get("FacilityLatitude"), fac.get("FacilityLongitude")
        if not flat or not flon:
            continue
        flat, flon = float(flat), float(flon)
        distance = _miles(lat, lon, flat, flon)
        if distance > radius_mi:
            continue
        if _is_closed(flat, flon, fs_sites):
            closed += 1
            continue
        name = str(fac.get("FacilityName") or UNKNOWN)
        reservable = bool(fac.get("Reservable"))
        camps.append(
            {
                "name": name.title() if name.isupper() else name,
                "distance_mi": round(distance, 1),
                "booking": "Dispersed" if dispersed else "Reservable" if reservable else "First come",
                "reservable": reservable,
                "dispersed": dispersed,
                "stay_limit": fac.get("StayLimit") or None,
                "phone": fac.get("FacilityPhone") or None,
                "url": f"https://www.recreation.gov/camping/campgrounds/{fac.get('FacilityID')}",
                "directions_url": (
                    f"https://www.google.com/maps/dir/?api=1&destination={flat},{flon}"
                ),
            }
        )
    camps.sort(key=lambda c: c["distance_mi"])
    return {
        "count": len(camps),
        "nearest": camps[0]["name"] if camps else None,
        "nearest_distance_mi": camps[0]["distance_mi"] if camps else None,
        "campgrounds": camps[:MAX_CAMPGROUNDS_LISTED],
        "closed_hidden": closed,
        "radius_mi": radius_mi,
        "attribution": RIDB_ATTRIBUTION,
    }
