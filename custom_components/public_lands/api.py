"""Look up who manages the land at a coordinate."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from . import const
from .codes import DESIGNATION_TYPE, FEAT_CLASS, MANAGER_NAME, MANAGER_TYPE
from .const import (
    ACCESS_MAP,
    COORD_PRECISION,
    NEARBY_DISTANCE_M,
    NON_PROTECTED_AREA,
    PADUS_FIELDS,
    PADUS_QUERY_URL,
    PRIVATE_LAND,
    REQUEST_TIMEOUT,
    SMA_FIELDS,
    SMA_QUERY_URL,
    SOURCE_PADUS,
    SOURCE_PADUS_NEARBY,
    SOURCE_SMA,
    UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)

# Order used to pick the main area when several overlap. This reproduces the
# choice made by the flattened PAD-US "Public Access" layer used before v0.3.0:
# a special designation (Wilderness, Scenic Area, ...) wins over the land
# parcel underneath it, and the smallest area wins a tie.
CATEGORY_PRIORITY: dict[str, int] = {
    "Designation": 0,
    "Fee": 1,
    "Easement": 2,
    "Marine": 3,
}

_DOD = ("Department of Defense", "Federal", frozenset({"DOD"}))
_STATE_CODES = frozenset({"SPR", "SDC", "SLB", "SFW", "SDNR", "SDOL", "OTHS"})
_LOCAL_CODES = frozenset({"CITY", "CNTY", "UNKL", "REG", "RWD"})

# BLM surface manager code -> (name, management type, matching PAD-US manager codes)
SMA_AGENCIES: dict[str, tuple[str, str, frozenset[str]]] = {
    "BLM": ("Bureau of Land Management", "Federal", frozenset({"BLM"})),
    "USFS": ("Forest Service", "Federal", frozenset({"USFS"})),
    "NPS": ("National Park Service", "Federal", frozenset({"NPS"})),
    "FWS": ("U.S. Fish and Wildlife Service", "Federal", frozenset({"FWS"})),
    "USBR": ("Bureau of Reclamation", "Federal", frozenset({"USBR"})),
    "BIA": ("Bureau of Indian Affairs", "American Indian Lands", frozenset({"BIA", "TRIB"})),
    "USACE": ("Army Corps of Engineers", "Federal", frozenset({"USACE"})),
    "DOD": _DOD,
    "ARMY": _DOD,
    "NAVY": _DOD,
    "USAF": _DOD,
    "USMC": _DOD,
    "DOE": ("Department of Energy", "Federal", frozenset({"DOE"})),
    "BPA": ("Bonneville Power Administration", "Federal", frozenset({"BPA"})),
    "NOAA": (
        "National Oceanic and Atmospheric Administration",
        "Federal",
        frozenset({"NOAA"}),
    ),
    "ST": ("State Land", "State", _STATE_CODES),
    "LG": ("Local Government Land", "Local Government", _LOCAL_CODES),
    "NTVALL": ("Alaska Native Land", "American Indian Lands", frozenset()),
    "NTVPIC": ("Alaska Native Land", "American Indian Lands", frozenset()),
}
OTHER_FEDERAL: tuple[str, str, frozenset[str]] = (
    "Other Federal Land",
    "Federal",
    frozenset({"OTHF"}),
)
# "UND" is BLM's label for land it has not classified, which is almost always private.
SMA_PRIVATE: dict[str, str] = {"PVT": "Private", "UND": "Undetermined"}


class PublicLandsError(Exception):
    """Raised when a lookup fails."""


class InvalidApiKey(PublicLandsError):
    """Raised when a service rejects the API key."""


def _decode(table: dict[str, str], code: Any) -> str:
    if code in (None, ""):
        return UNKNOWN
    return table.get(str(code), str(code))


def decode_area(attrs: dict[str, Any]) -> dict[str, Any]:
    """Turn one PAD-US record into readable values."""
    return {
        "unit_name": attrs.get("Unit_Nm") or UNKNOWN,
        "category": _decode(FEAT_CLASS, attrs.get("FeatClass")),
        "management_type": _decode(MANAGER_TYPE, attrs.get("Mang_Type")),
        "management_name": _decode(MANAGER_NAME, attrs.get("Mang_Name")),
        "designation": _decode(DESIGNATION_TYPE, attrs.get("Des_Tp")),
        "public_access": ACCESS_MAP.get(attrs.get("Pub_Access"), UNKNOWN),
        "acres": attrs.get("GIS_Acres"),
        "feature_class_code": attrs.get("FeatClass"),
        "manager_code": attrs.get("Mang_Name"),
    }


def _sort_key(area: dict[str, Any]) -> tuple[int, float]:
    acres = area.get("acres")
    return (
        CATEGORY_PRIORITY.get(area.get("feature_class_code") or "", 9),
        float(acres) if isinstance(acres, (int, float)) else float("inf"),
    )


def _base_result(lat: float, lon: float) -> dict[str, Any]:
    return {
        "latitude": lat,
        "longitude": lon,
        "source": SOURCE_PADUS,
        "unit_name": NON_PROTECTED_AREA,
        "public_access": UNKNOWN,
        "management_type": UNKNOWN,
        "management_name": UNKNOWN,
        "designation": UNKNOWN,
        "underlying_land": None,
        "surface_manager": None,
        "areas": [],
    }


def _apply_areas(result: dict[str, Any], areas: list[dict[str, Any]]) -> dict[str, Any]:
    primary = areas[0]
    for key in (
        "unit_name",
        "public_access",
        "management_type",
        "management_name",
        "designation",
    ):
        result[key] = primary[key]
    if primary.get("feature_class_code") != "Fee":
        fee = next((a for a in areas if a.get("feature_class_code") == "Fee"), None)
        result["underlying_land"] = fee["unit_name"] if fee else None
    result["areas"] = [
        {k: v for k, v in a.items() if k not in ("feature_class_code", "manager_code")}
        for a in areas
    ]
    return result


class PublicLandsClient:
    """Query PAD-US, falling back to BLM's surface management map."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_lookup(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Return land details for a coordinate. Raises PublicLandsError on failure."""
        lat = round(float(latitude), COORD_PRECISION)
        lon = round(float(longitude), COORD_PRECISION)
        result = _base_result(lat, lon)

        features = await self._query(PADUS_QUERY_URL, lat, lon, PADUS_FIELDS)
        areas = sorted((decode_area(f.get("attributes") or {}) for f in features), key=_sort_key)
        if areas:
            return _apply_areas(result, areas)

        # PAD-US has nothing here: ask BLM who manages the surface.
        try:
            sma = await self._query(SMA_QUERY_URL, lat, lon, SMA_FIELDS)
        except PublicLandsError as err:
            _LOGGER.debug("Surface management lookup failed: %s", err)
            return result
        code = (sma[0].get("attributes") or {}).get("ADMIN_AGENCY_CODE") if sma else None
        if not code:
            return result

        result["source"] = SOURCE_SMA
        if code in SMA_PRIVATE:
            result["surface_manager"] = SMA_PRIVATE[code]
            result.update(
                unit_name=PRIVATE_LAND,
                public_access=PRIVATE_LAND,
                management_type="Private",
                management_name="Private",
                designation=PRIVATE_LAND,
            )
            return result

        name, mang_type, padus_codes = SMA_AGENCIES.get(code, OTHER_FEDERAL)
        result["surface_manager"] = name

        # Public land that PAD-US misses (road corridors, small gaps): use a nearby
        # PAD-US area, but only if BLM agrees on who manages it.
        if padus_codes:
            try:
                nearby = await self._query(
                    PADUS_QUERY_URL, lat, lon, PADUS_FIELDS, distance=NEARBY_DISTANCE_M
                )
            except PublicLandsError as err:
                _LOGGER.debug("Nearby PAD-US lookup failed: %s", err)
                nearby = []
            matches = sorted(
                (
                    a
                    for a in (decode_area(f.get("attributes") or {}) for f in nearby)
                    if a.get("manager_code") in padus_codes
                ),
                key=_sort_key,
            )
            if matches:
                result["source"] = SOURCE_PADUS_NEARBY
                return _apply_areas(result, matches)

        result.update(unit_name=name, management_type=mang_type, management_name=name)
        return result

    async def _query(
        self,
        url: str,
        lat: float,
        lon: float,
        out_fields: str,
        distance: int | None = None,
    ) -> list[dict[str, Any]]:
        return await arcgis_point_query(
            self._session, url, lat, lon, out_fields, distance=distance
        )


async def get_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, str],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """GET a JSON object, retrying once. Raises PublicLandsError on failure.

    ArcGIS reports errors inside a normal HTTP 200 response, so an "error" key
    in the body also counts as a failure. HTTP 401 raises InvalidApiKey without
    retrying.
    """
    last_error: Exception | None = None
    for attempt in range(2):
        if attempt:
            await asyncio.sleep(const.RETRY_DELAY)
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidApiKey("The API key was rejected")
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            last_error = err
            continue
        if not isinstance(data, dict):
            last_error = PublicLandsError("Unexpected response")
            continue
        if "error" in data:
            error = data["error"] if isinstance(data["error"], dict) else {}
            last_error = PublicLandsError(
                f"Service error {error.get('code')}: {error.get('message')}"
            )
            continue
        return data

    raise PublicLandsError(str(last_error) or type(last_error).__name__)


async def arcgis_point_query(
    session: aiohttp.ClientSession,
    url: str,
    lat: float,
    lon: float,
    out_fields: str,
    distance: int | None = None,
) -> list[dict[str, Any]]:
    """Return the features of an ArcGIS layer at (or near) a point."""
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": out_fields,
        "returnGeometry": "false",
        "f": "json",
    }
    if distance:
        params["distance"] = str(distance)
        params["units"] = "esriSRUnit_Meter"
    data = await get_json(session, url, params)
    features = data.get("features")
    if not isinstance(features, list):
        raise PublicLandsError("Response has no features")
    return features
