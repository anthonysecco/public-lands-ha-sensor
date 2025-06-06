from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN

class PublicLandsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="US Public Lands", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional("enabled", default=True): bool,
            }),
        )

    async def async_step_import(self, import_data=None):
        return self.async_create_entry(title="US Public Lands", data={"enabled": True})

    @staticmethod
    def async_get_options_flow(config_entry):
        return PublicLandsOptionsFlow(config_entry)

class PublicLandsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        current = self.config_entry.options.get("enabled", True)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("enabled", default=current): bool,
            }),
        )
