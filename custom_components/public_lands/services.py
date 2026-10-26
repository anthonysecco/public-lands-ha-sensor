"""Actions for Public Lands."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import PublicLandsError
from .const import DOMAIN

SERVICE_LOOKUP = "lookup"

LOOKUP_SCHEMA = vol.Schema(
    {
        vol.Inclusive(ATTR_LATITUDE, "coordinates"): cv.latitude,
        vol.Inclusive(ATTR_LONGITUDE, "coordinates"): cv.longitude,
    }
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register public_lands.lookup.

    Looks up any coordinate (or the current location) and returns the result
    without changing the sensors, e.g. to check a destination before driving.
    """

    async def _async_lookup(call: ServiceCall) -> ServiceResponse:
        coordinators = list(hass.data.get(DOMAIN, {}).values())
        if not coordinators:
            raise ServiceValidationError("Public Lands is not set up")
        coordinator = coordinators[0]

        if ATTR_LATITUDE in call.data:
            lat, lon = call.data[ATTR_LATITUDE], call.data[ATTR_LONGITUDE]
        else:
            try:
                lat, lon = coordinator.current_location()
            except UpdateFailed as err:
                raise HomeAssistantError(str(err)) from err

        try:
            return await coordinator.client.async_lookup(lat, lon)
        except PublicLandsError as err:
            raise HomeAssistantError(f"Public lands lookup failed: {err}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP,
        _async_lookup,
        schema=LOOKUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
