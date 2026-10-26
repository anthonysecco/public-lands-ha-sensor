"""Refresh button for Public Lands."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PublicLandsCoordinator
from .entity import PublicLandsEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PublicLandsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RefreshUSPLButton(coordinator)])


class RefreshUSPLButton(PublicLandsEntity, ButtonEntity):
    """Look up the land at the current location."""

    _attr_name = "Refresh USPL"
    _attr_unique_id = "refresh_uspl"
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
