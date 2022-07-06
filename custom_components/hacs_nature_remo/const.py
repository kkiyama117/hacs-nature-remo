# Should be equal to the name of your component.
from datetime import timedelta
from logging import Logger, getLogger

PLATFORMS: any = {"sensor", "climate", "light", "switch"}
DOMAIN: str = "hacs_nature_remo"

LOGGER: Logger = getLogger(__package__)

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)
