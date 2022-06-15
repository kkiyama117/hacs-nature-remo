# from typing import Any
#
# from homeassistant import config_entries
# from .const import *
# import voluptuous as vol
#
#
# class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Example config flow."""
#
#     async def async_step_user(self, info: dict[str, Any] | None = None):
#         if info is not None:
#             pass  # TODO: process info
#
#         return self.async_show_form(
#             step_id="user", data_schema=vol.Schema({vol.Required("password"): str})
#         )
