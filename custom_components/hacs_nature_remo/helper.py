from homeassistant.const import CONF_ACCESS_TOKEN
from remo import NatureRemoAPI

from custom_components.hacs_nature_remo import DOMAIN


def get_api_base(hass):
    access_token = hass.data.get(DOMAIN)[CONF_ACCESS_TOKEN]
    api = NatureRemoAPI(access_token)
    return api
