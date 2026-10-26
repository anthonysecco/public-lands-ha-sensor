"""Sensors for Public Lands."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import STATUS_OK, PublicLandsCoordinator
from .entity import PublicLandsEntity

# (unique id key, name, icon, result field). Unique IDs and names are unchanged
# from v0.2.x so existing entity IDs (sensor.uspl_unit_name, ...) are kept.
LAND_SENSORS: tuple[tuple[str, str, str, str], ...] = (
    ("Unit_Nm", "Unit Name", "mdi:map-marker-radius", "unit_name"),
    ("Pub_Access", "Public Access", "mdi:key", "public_access"),
    ("MngTp_Desc", "Management Type", "mdi:account-tie-hat", "management_type"),
    ("MngNm_Desc", "Management Name", "mdi:domain", "management_name"),
    ("DesTp_Desc", "Designation", "mdi:pine-tree", "designation"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PublicLandsCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[PublicLandsEntity] = [
        PublicLandsSensor(coordinator, *definition) for definition in LAND_SENSORS
    ]
    entities.append(LastSuccessSensor(coordinator))
    # API Status is a binary sensor registered on the sensor platform, as in
    # v0.2.x. Moving it would change its entity ID (sensor.uspl_api_status).
    entities.append(PublicLandsStatusBinarySensor(coordinator))
    async_add_entities(entities)


class PublicLandsSensor(PublicLandsEntity, SensorEntity):
    """One field of the current land lookup."""

    _unrecorded_attributes = frozenset({"overlapping_areas"})

    def __init__(
        self,
        coordinator: PublicLandsCoordinator,
        key: str,
        name: str,
        icon: str,
        field: str,
    ) -> None:
        self._field = field
        self._attr_name = f"USPL {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"uspl_{key}"
        super().__init__(coordinator, SENSOR_DOMAIN)

    @property
    def native_value(self) -> str | None:
        data = self.coordinator.data
        if not data:
            return None
        return data.get(self._field)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data
        if self._field != "unit_name" or not data:
            return None
        return {
            "source": data.get("source"),
            "underlying_land": data.get("underlying_land"),
            "surface_manager": data.get("surface_manager"),
            "overlapping_areas": [
                f"{a['unit_name']} ({a['category']}, {a['management_name']})"
                for a in data.get("areas", [])
            ],
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "location_entity": data.get("location_entity"),
        }


class LastSuccessSensor(PublicLandsEntity, SensorEntity):
    """Time of the last successful refresh."""

    _attr_name = "USPL Last Successful Refresh"
    _attr_unique_id = "uspl_last_success"
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: PublicLandsCoordinator) -> None:
        super().__init__(coordinator, SENSOR_DOMAIN)

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_success


class PublicLandsStatusBinarySensor(PublicLandsEntity, BinarySensorEntity):
    """On when the last refresh succeeded."""

    _attr_name = "USPL API Status"
    _attr_unique_id = "uspl_api_status"
    _attr_icon = "mdi:check-network"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: PublicLandsCoordinator) -> None:
        # Registered on the sensor platform, so its ID is sensor.uspl_api_status.
        super().__init__(coordinator, SENSOR_DOMAIN)

    @property
    def is_on(self) -> bool:
        return self.coordinator.status == STATUS_OK

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self.coordinator.last_success
        return {"last_success": last.isoformat(timespec="seconds") if last else "Never"}
