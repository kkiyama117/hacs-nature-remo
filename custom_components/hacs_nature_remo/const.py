# Should be equal to the name of your component.
from logging import Logger, getLogger

PLATFORMS: any = {"sensor"}
DOMAIN: str = "hacs_nature_remo"

LOGGER: Logger = getLogger(__package__)

DEFAULT_GET_INTERVAL: int = 60
