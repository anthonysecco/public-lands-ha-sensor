from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault("sensors", [])
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, "sensor")
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, "button")
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_sensor = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    unload_button = await hass.config_entries.async_forward_entry_unload(entry, "button")
    return unload_sensor and unload_button
