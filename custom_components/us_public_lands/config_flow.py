from homeassistant import config_entries
from .const import DOMAIN

class PublicLandsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Public Lands."""

    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="Public Lands", data={})
