"""Data coordinator for Public Lands."""

from __future__ import annotations

from collections.abc import Awaitable
from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import InvalidApiKey, PublicLandsClient, PublicLandsError
from .const import (
    CONF_CAMPGROUNDS,
    CONF_CITY_COUNTY,
    CONF_LOCATION_ENTITY,
    CONF_RIDB_API_KEY,
    CONF_SEARCH_RADIUS,
    DEFAULT_LOCATION_ENTITY,
    DEFAULT_SEARCH_RADIUS,
    DOMAIN,
    FEATURE_CAMPGROUNDS,
    FEATURE_CITY_COUNTY,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .extras import async_campgrounds, async_city_county, async_rules_link

_LOGGER = logging.getLogger(__name__)

STATUS_OK = "ok"
STATUS_FAIL = "fail"


class PublicLandsCoordinator(DataUpdateCoordinator[dict[str, Any] | None]):
    """Fetch land data on demand and keep the last result across restarts.

    There is no polling: a refresh happens when the button is pressed (usually
    from an automation). Failed refreshes keep the previous values.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        self.client = PublicLandsClient(async_get_clientsession(hass))
        self.status: str | None = None
        self.last_success: datetime | None = None
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    @property
    def location_entity(self) -> str:
        """Entity whose coordinates are looked up."""
        return self.entry.options.get(CONF_LOCATION_ENTITY) or DEFAULT_LOCATION_ENTITY

    async def async_load(self) -> None:
        """Restore the last result saved before a restart."""
        stored = await self._store.async_load()
        if not isinstance(stored, dict):
            return
        self.data = stored.get("result")
        self.status = stored.get("status")
        if last := stored.get("last_success"):
            self.last_success = dt_util.parse_datetime(last)

    def current_location(self) -> tuple[float, float]:
        """Return the latitude and longitude of the location entity."""
        entity_id = self.location_entity
        if (state := self.hass.states.get(entity_id)) is not None:
            lat = state.attributes.get(ATTR_LATITUDE)
            lon = state.attributes.get(ATTR_LONGITUDE)
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        if entity_id == DEFAULT_LOCATION_ENTITY:
            _LOGGER.warning("zone.home not found, using configured coordinates")
            return self.hass.config.latitude, self.hass.config.longitude
        raise UpdateFailed(f"{entity_id} has no latitude and longitude")

    def feature_enabled(self, feature: str) -> bool:
        """Whether an optional feature is switched on under Configure."""
        if feature == FEATURE_CAMPGROUNDS:
            return bool(
                self.entry.options.get(CONF_CAMPGROUNDS)
                and self.entry.options.get(CONF_RIDB_API_KEY)
            )
        option = {FEATURE_CITY_COUNTY: CONF_CITY_COUNTY}[feature]
        return bool(self.entry.options.get(option))

    async def async_lookup(self, latitude: float, longitude: float) -> dict[str, Any]:
        """Land lookup plus any optional features that are switched on.

        Raises PublicLandsError if the main land lookup fails. A failed optional
        lookup is logged and left empty so it never hides the land result.
        """
        result = await self.client.async_lookup(latitude, longitude)
        lat, lon = result["latitude"], result["longitude"]
        session = async_get_clientsession(self.hass)
        options = self.entry.options
        # Link to the managing office's rules page, shown as attributes on
        # USPL Management Name. A failure here never fails the refresh.
        result["rules_link"] = await self._optional(
            "rules link", async_rules_link(session, lat, lon, result)
        )

        extras: dict[str, Any] = {}
        if self.feature_enabled(FEATURE_CITY_COUNTY):
            extras[FEATURE_CITY_COUNTY] = await self._optional(
                FEATURE_CITY_COUNTY, async_city_county(session, lat, lon)
            )
        if self.feature_enabled(FEATURE_CAMPGROUNDS):
            radius = float(options.get(CONF_SEARCH_RADIUS) or DEFAULT_SEARCH_RADIUS)
            extras[FEATURE_CAMPGROUNDS] = await self._optional(
                FEATURE_CAMPGROUNDS,
                async_campgrounds(session, options[CONF_RIDB_API_KEY], lat, lon, radius),
            )

        result["extras"] = extras
        return result

    async def _optional(self, feature: str, lookup: Awaitable[Any]) -> Any:
        try:
            return await lookup
        except InvalidApiKey:
            _LOGGER.warning(
                "Recreation.gov rejected the API key; update it under Configure"
            )
        except PublicLandsError as err:
            _LOGGER.warning("Public Lands %s lookup failed: %s", feature, err)
        return None

    async def _async_update_data(self) -> dict[str, Any] | None:
        try:
            lat, lon = self.current_location()
            result = await self.async_lookup(lat, lon)
        except (PublicLandsError, UpdateFailed) as err:
            self.status = STATUS_FAIL
            await self._async_save(self.data)
            raise UpdateFailed(f"Failed to fetch public lands data: {err}") from err

        result["location_entity"] = self.location_entity
        self.status = STATUS_OK
        self.last_success = dt_util.now()
        await self._async_save(result)
        return result

    async def _async_save(self, result: dict[str, Any] | None) -> None:
        await self._store.async_save(
            {
                "result": result,
                "status": self.status,
                "last_success": self.last_success.isoformat() if self.last_success else None,
            }
        )
