import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFINITIONS = {
    "Unit_Nm": ("Unit Name", "mdi:map-marker-radius"),
    "Pub_Access": ("Public Access", "mdi:key"),
    "MngTp_Desc": ("Management Type", "mdi:account-tie-hat"),
    "MngNm_Desc": ("Management Name", "mdi:domain"),
    "DesTp_Desc": ("Designation", "mdi:pine-tree"),
}

ACCESS_MAP = {
    "OA": "Open to the Public",
    "RA": "Restricted Access",
    "XA": "Closed to the Public",
    "PA": "Public Access by Permit",
    "TA": "Temporary Access Allowed",
    "UK": "Unknown"
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    hass.data.setdefault(DOMAIN, {}).setdefault("sensors", [])
    entities: list = []

    # Create standard USPL data sensors
    for key, (name, icon) in SENSOR_DEFINITIONS.items():
        sensor = PublicLandsSensor(hass, name, icon, key)
        hass.data[DOMAIN]["sensors"].append(sensor)
        entities.append(sensor)

    # Create and register the status and last_success sensors
    status_sensor = PublicLandsStatusBinarySensor(hass)
    last_success_sensor = LastSuccessSensor(hass)

    hass.data[DOMAIN]["status_sensor"] = status_sensor
    hass.data[DOMAIN]["last_success_sensor"] = last_success_sensor

    entities.append(last_success_sensor)
    entities.append(status_sensor)

    # Register all sensors at once
    async_add_entities(entities, True)


class PublicLandsSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, name: str, icon: str, key: str):
        self.hass = hass
        self._attr_name = f"USPL {name}"
        self._attr_icon = icon
        self._key = key
        self._attr_unique_id = f"uspl_{key}"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def state(self):
        raw_data = self.hass.data.get(DOMAIN, {}).get("latest_api_data", {})
        attributes = (raw_data.get("features") or [{}])[0].get("attributes", {})
        value = attributes.get(self._key)

        if self._key == "Unit_Nm" and value == "Non-PAD-US Area":
            return "Non-Protected Area"
        if self._key == "Pub_Access":
            return ACCESS_MAP.get(value, "Unknown Access Type")
        return value or "Unavailable"


class LastSuccessSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._attr_name = "USPL Last Successful Refresh"
        self._attr_unique_id = "uspl_last_success"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_class = "timestamp"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def state(self):
        return self.hass.data.get(DOMAIN, {}).get("last_success", "Never")


class PublicLandsStatusBinarySensor(BinarySensorEntity):
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._attr_name = "USPL API Status"
        self._attr_unique_id = "uspl_api_status"
        self._attr_icon = "mdi:check-network"
        self._attr_device_class = "connectivity"

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self.hass.data.get(DOMAIN, {}).get("status") == "ok"

    @property
    def extra_state_attributes(self):
        return {
            "last_success": self.hass.data.get(DOMAIN, {}).get("last_success", "Never")
        }
