import aiohttp
import async_timeout
import logging
from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    # Ensure the shared sensor list exists
    hass.data.setdefault(DOMAIN, {}).setdefault("sensors", [])

    # Create and register the refresh button
    button = RefreshUSPLButton(hass, hass.data[DOMAIN]["sensors"])
    async_add_entities([button], True)


class RefreshUSPLButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, sensors: list):
        """Initialize the button with a handle to hass and the sensor list."""
        self.hass = hass
        self._sensors = sensors
        self._attr_name = "Refresh USPL"
        self._attr_unique_id = "refresh_uspl"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        _LOGGER.debug("USPL refresh button pressed")

        # Get location from zone.home or fallback to configured lat/lon
        zone = self.hass.states.get("zone.home")
        if zone:
            lat = round(zone.attributes.get("latitude"), 4)
            lon = round(zone.attributes.get("longitude"), 4)
        else:
            _LOGGER.warning("zone.home not found, using configured coords")
            lat = round(self.hass.config.latitude, 4)
            lon = round(self.hass.config.longitude, 4)

        url = (
            f"https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/"
            f"PADUS_Public_Access/FeatureServer/0/query?"
            f"geometry={lon},{lat}&geometryType=esriGeometryPoint&inSR=4326"
            f"&outFields=Unit_Nm,Pub_Access,MngTp_Desc,MngNm_Desc,DesTp_Desc"
            f"&returnGeometry=false&f=json"
        )

        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()

                        # Store data and update status
                        self.hass.data[DOMAIN]["latest_api_data"] = data
                        self.hass.data[DOMAIN]["last_success"] = dt_util.now().isoformat(timespec="seconds")
                        self.hass.data[DOMAIN]["status"] = "ok"
                        _LOGGER.info("USPL data refreshed successfully")

        except Exception as e:
            self.hass.data[DOMAIN]["status"] = "fail"
            _LOGGER.error(f"Failed to fetch public lands data: {e}")
            return

        #  Refresh main USPL sensors
        for sensor in self._sensors:
            sensor.async_schedule_update_ha_state()

        #  Also refresh status/last_success sensors if available
        if "last_success_sensor" in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["last_success_sensor"].async_schedule_update_ha_state()

        if "status_sensor" in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN]["status_sensor"].async_schedule_update_ha_state()
