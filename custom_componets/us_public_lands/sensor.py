from datetime import datetime, timedelta
import logging
import aiohttp
import async_timeout

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)

USPL_KEYS = {
    "DesTp_Desc": "Designation",
    "MngNm_Desc": "Management Name",
    "MngTp_Desc": "Management Type",
    "Pub_Access": "Public Access",
    "Unit_Nm": "Unit Name"
}

class PublicLandsSensor(SensorEntity):
    def __init__(self, name, key, data):
        self._attr_name = f"US Public Lands: {name}"
        self._attr_unique_id = f"uspl_{key}"
        self._key = key
        self._data = data
        self._attr_icon = "mdi:map-marker"

    @property
    def state(self):
        return self._data.get(self._key, "Unavailable")

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    zone = hass.states.get("zone.home")
    if not zone:
        _LOGGER.error("zone.home not found.")
        return

    lat = zone.attributes.get("latitude")
    lon = zone.attributes.get("longitude")
    if not lat or not lon:
        _LOGGER.error("zone.home missing coordinates.")
        return

    url = f"https://www.uspubliclands.com/api/v1/location/{lat},{lon}.json"
    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.json()
                    public_data = data.get("land", {})
    except Exception as e:
        _LOGGER.error(f"Failed to fetch public lands data: {e}")
        return

    sensors = [
        PublicLandsSensor(name, key, public_data)
        for key, name in USPL_KEYS.items()
    ]
    async_add_entities(sensors, update_before_add=True)
