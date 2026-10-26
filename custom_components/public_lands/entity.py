"""Base entity for Public Lands."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import DOMAIN
from .coordinator import PublicLandsCoordinator


class PublicLandsEntity(CoordinatorEntity[PublicLandsCoordinator]):
    """Shared device info. Entities stay available and keep their last values
    when a refresh fails; the API Status sensor reports the failure."""

    def __init__(self, coordinator: PublicLandsCoordinator, domain: str) -> None:
        super().__init__(coordinator)
        # Request the v0.2.x entity ID ("sensor.uspl_unit_name", "button.refresh_uspl").
        # Without this, new installs would get the device name as a prefix. Existing
        # installs keep whatever ID the entity registry already has.
        self.entity_id = f"{domain}.{slugify(self._attr_name)}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Public Lands",
            manufacturer="USGS PAD-US / BLM",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://github.com/anthonysecco/public-lands-ha-sensor",
        )

    @property
    def available(self) -> bool:
        return True
