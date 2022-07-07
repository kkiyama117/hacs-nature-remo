from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Coroutine, Mapping, Optional

from remo import NatureRemoError
from remo.models import *

BASE_URL = "https://api.nature.global"
__version__ = ""
__url__ = ""


class HTTPMethod(Enum):
    GET = auto()
    POST = auto()


class Request(ABC):
    pass


class Response(ABC):
    @property
    @abstractmethod
    def headers(self) -> Mapping:
        pass

    @property
    @abstractmethod
    def status_code(self) -> any:
        pass

    @property
    @abstractmethod
    def reason(self) -> str | None:
        pass

    @abstractmethod
    async def json(self):
        pass

    @property
    @abstractmethod
    def ok(self):
        pass


class HTTPWrapper(ABC):
    @abstractmethod
    async def get(self, url, headers=None) -> Response:
        pass

    @abstractmethod
    async def post(self, url, headers=None, data=None) -> Response:
        pass


def enable_debug_mode():
    import logging
    from http.client import HTTPConnection

    HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)


async def build_error_message(resp: Response) -> str:
    error = await resp.json()
    return (
            f"HTTP Status Code: {resp.status_code}, "
            + f'Nature Remo Code: {error["code"]}, Message: {error["message"]}'
    )


@dataclass
class RateLimit:
    checked_at: Optional[datetime] = None
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset: Optional[datetime] = None


class NatureRemoAPIVer1:
    """Client for the Nature Remo API."""

    def __init__(self, inner: HTTPWrapper, access_token: str, debug: bool = False):
        if debug:
            enable_debug_mode()
        self._inner = inner
        self._endpoint_base = "/1"
        self.access_token = access_token
        self.base_url = BASE_URL
        self.rate_limit = RateLimit()

    def __request(self, endpoint: str, method: HTTPMethod, data: dict = None
                  ) -> Coroutine[Any, Any, Response]:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"nature-remo/{__version__} ({__url__})",
        }

        url = f"{self.base_url}{endpoint}"

        try:
            if method == HTTPMethod.GET:
                return self._inner.get(url, headers=headers)
            else:
                return self._inner.post(url, headers=headers, data=data)
        except OSError as e:
            raise NatureRemoError(e)

    def __get_json(self, resp: Response) -> Coroutine[Any, Any, Any]:
        self.__set_rate_limit(resp)
        if resp.ok:
            return resp.json()
        raise NatureRemoError(build_error_message(resp))

    def __set_rate_limit(self, resp: Response):
        if "Date" in resp.headers:
            self.rate_limit.checked_at = datetime.strptime(
                resp.headers["Date"], "%a, %d %b %Y %H:%M:%S GMT"
            )
        if "X-Rate-Limit-Limit" in resp.headers:
            self.rate_limit.limit = int(resp.headers["X-Rate-Limit-Limit"])
        if "X-Rate-Limit-Remaining" in resp.headers:
            self.rate_limit.remaining = int(
                resp.headers["X-Rate-Limit-Remaining"]
            )
        if "X-Rate-Limit-Reset" in resp.headers:
            self.rate_limit.reset = datetime.utcfromtimestamp(
                int(resp.headers["X-Rate-Limit-Reset"])
            )

    async def get_user(self) -> User:
        """Fetch the authenticated user's information.

        Returns:
            A User object.
        """
        endpoint = f"{self._endpoint_base}/users/me"
        resp = await self.__request(endpoint, HTTPMethod.GET)
        json = await self.__get_json(resp)
        return UserSchema().load(json)

    async def update_user(self, nickname: str) -> User:
        """Update authenticated user's information.

        Args:
            nickname: User's nickname.

        Returns:
            A User object.
        """
        endpoint = f"{self._endpoint_base}/users/me"
        resp = await self.__request(
            endpoint, HTTPMethod.POST, {"nickname": nickname}
        )
        json = await self.__get_json(resp)
        return UserSchema().load(json)

    async def get_devices(self) -> List[Device]:
        """Fetch the list of Remo devices the user has access to.

        Returns:
            A List of Device objects.
        """
        endpoint = f"{self._endpoint_base}/devices"
        resp = await self.__request(endpoint, HTTPMethod.GET)
        json = await self.__get_json(resp)
        return DeviceSchema(many=True).load(json)

    async def update_device(self, device: str, name: str):
        """Update Remo.

        Args:
            device: Device ID.
            name: Device name.
        """
        endpoint = f"{self._endpoint_base}/devices/{device}"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"name": name})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def delete_device(self, device: str):
        """Delete Remo.

        Args:
            device: Device ID.
        """
        endpoint = f"{self._endpoint_base}/devices/{device}/delete"
        resp = await self.__request(endpoint, HTTPMethod.POST)
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def update_temperature_offset(self, device: str, offset: int):
        """Update temperature offset.

        Args:
            device: Device ID.
            offset: Temperature offset value added to the measured temperature.
        """
        endpoint = f"{self._endpoint_base}/devices/{device}/temperature_offset"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"offset": offset})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def update_humidity_offset(self, device: str, offset: int):
        """Update humidity offset.

        Args:
            device: Device ID.
            offset: Humidity offset value added to the measured humidity.
        """
        endpoint = f"{self._endpoint_base}/devices/{device}/humidity_offset"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"offset": offset})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def detect_appliance(self, message: str) -> List[ApplianceModelAndParams]:
        """Find the air conditioner best matching the provided infrared signal.

        Args:
            message: JSON serialized object describing infrared signals.
              Includes "data", "freq" and "format" keys.
        """
        endpoint = f"{self._endpoint_base}/detectappliance"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"message": message})
        json = await self.__get_json(resp)
        return ApplianceModelAndParamsSchema(many=True).load(json)

    async def get_appliances(self) -> List[Appliance]:
        """Fetch the list of appliances.

        Returns:
            A list of Appliance objects.
        """
        endpoint = f"{self._endpoint_base}/appliances"
        resp = await self.__request(endpoint, HTTPMethod.GET)
        json = await self.__get_json(resp)
        return ApplianceSchema(many=True).load(json)

    async def create_appliance(
            self,
            device: str,
            nickname: str,
            image: str,
            model: str = None,
            model_type: str = None,
    ) -> Appliance:
        """Create a new appliance.

        Args:
            device: Device ID.
            nickname: Appliance name.
            image: Basename of the image file included in the app.
            model: ApplianceModel ID if the appliance we're trying to create
              is included in IRDB.
            model_type: Type of model.
        """
        endpoint = f"{self._endpoint_base}/appliances"
        data = {"device": device, "nickname": nickname, "image": image}
        if model:
            data["model"] = model
        if model_type:
            data["model_type"] = model_type
        resp = await self.__request(endpoint, HTTPMethod.POST, data)
        json = await self.__get_json(resp)
        return ApplianceSchema().load(json)

    async def update_appliance_orders(self, appliances: str):
        """Reorder appliances.

        Args:
            appliances: List of all appliances' IDs comma separated.
        """
        endpoint = f"{self._endpoint_base}/appliance_orders"
        resp = await self.__request(
            endpoint, HTTPMethod.POST, {"appliances": appliances}
        )
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def delete_appliance(self, appliance: str):
        """Delete appliance.

        Args:
            appliance: Appliance ID.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/delete"
        resp = await self.__request(endpoint, HTTPMethod.POST)
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def update_appliance(
            self, appliance: str, nickname: str, image: str
    ) -> Appliance:
        """Update appliance.

        Args:
            appliance: Appliance ID.
            nickname: Appliance name.
            image: Basename of the image file included in the app.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}"
        resp = await self.__request(
            endpoint, HTTPMethod.POST, {"nickname": nickname, "image": image}
        )
        json = await self.__get_json(resp)
        return ApplianceSchema().load(json)

    async def update_aircon_settings(
            self,
            appliance: str,
            operation_mode: str = None,
            temperature: str = None,
            air_volume: str = None,
            air_direction: str = None,
            button: str = None,
    ):
        """Update air conditioner settings.

        Args:
            appliance: Appliance ID.
            operation_mode: AC operation mode.
            temperature: Temperature.
            air_volume: AC air volume.
            air_direction: AC air direction.
            button: Button.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/aircon_settings"
        data = {}
        if operation_mode:
            data["operation_mode"] = operation_mode
        if temperature:
            data["temperature"] = temperature
        if air_volume:
            data["air_volume"] = air_volume
        if air_direction:
            data["air_direction"] = air_direction
        if button:
            data["button"] = button
        resp = await self.__request(endpoint, HTTPMethod.POST, data)
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def send_tv_infrared_signal(self, appliance: str, button: str):
        """Send tv infrared signal.

        Args:
            appliance: Appliance ID.
            button: Button name.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/tv"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"button": button})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def send_light_infrared_signal(self, appliance: str, button: str):
        """Send light infrared signal.

        Args:
            appliance: Appliance ID.
            button: Button name.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/light"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"button": button})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def get_signals(self, appliance: str) -> List[Signal]:
        """Fetch signals registered under this appliance.

        Args:
            appliance: Appliance ID.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/signals"
        resp = await self.__request(endpoint, HTTPMethod.GET)
        json = await self.__get_json(resp)
        return SignalSchema(many=True).load(json)

    async def create_signal(
            self, appliance: str, name: str, message: str, image: str
    ) -> Signal:
        """Create a signal under this appliance.

        Args:
            appliance: Appliance ID.
            name: Signal name.
            message: JSON serialized object describing infrared signals.
              Includes "data", "freq" and "format" keys.
            image: Basename of the image file included in the app.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/signals"
        resp = await self.__request(
            endpoint,
            HTTPMethod.POST,
            {"name": name, "message": message, "image": image},
        )
        json = await self.__get_json(resp)
        return SignalSchema().load(json)

    async def update_signal_orders(self, appliance: str, signals: str):
        """Reorder signals under this appliance.

        Args:
            appliance: Appliance ID.
            signals: List of all signals' IDs comma separated.
        """
        endpoint = f"{self._endpoint_base}/appliances/{appliance}/signal_orders"
        resp = await self.__request(endpoint, HTTPMethod.POST, {"signals": signals})
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def update_signal(self, signal: str, name: str, image: str):
        """Update infrared signal.

        Args:
            signal: Signal ID.
            name: Signal name.
            image: Basename of the image file included in the app.
        """
        endpoint = f"{self._endpoint_base}/signals/{signal}"
        resp = await self.__request(
            endpoint, HTTPMethod.POST, {"name": name, "image": image}
        )
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def delete_signal(self, signal: str):
        """Delete infrared signal.

        Args:
            signal: Signal ID.
        """
        endpoint = f"{self._endpoint_base}/signals/{signal}/delete"
        resp = await self.__request(endpoint, HTTPMethod.POST)
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))

    async def send_signal(self, signal: str):
        """Send infrared signal.

        Args:
            signal: Signal ID.
        """
        endpoint = f"{self._endpoint_base}/signals/{signal}/send"
        resp = await self.__request(endpoint, HTTPMethod.POST)
        if not resp.ok:
            raise NatureRemoError(build_error_message(resp))


class NatureRemoLocalAPIVer1:
    """Client for the Nature Remo Local API."""

    def __init__(self, inner: HTTPWrapper, addr: str, debug: bool = False):
        if debug:
            enable_debug_mode()
        self.addr = addr
        self._inner = inner

    def __request(
            self, endpoint: str, method: HTTPMethod, data: str = None
    ) -> Coroutine[Any, Any, Response]:
        headers = {
            "Accept": "application/json",
            "X-Requested-With": f"nature-remo/{__version__} ({__url__})",
        }
        url = f"http://{self.addr}{endpoint}"

        try:
            if method == HTTPMethod.GET:
                return self._inner.get(url, headers=headers)
            else:
                return self._inner.post(url, headers=headers, data=data)
        except OSError as e:
            raise NatureRemoError(e)

    def __get_json(self, resp: Response) -> Coroutine[Any, Any, Any]:
        if resp.ok:
            return resp.json()
        raise NatureRemoError(f"{resp.status_code} {resp.reason}")

    async def get_ir_signal(self) -> IRSignal:
        """Fetch the newest received IR signal.

        Returns:
            An IRSignal object.
        """
        endpoint = "/messages"
        resp = await self.__request(endpoint, HTTPMethod.GET)
        json = await self.__get_json(resp)
        return IRSignalSchema().load(json)

    async def send_ir_signal(self, message: str):
        """Emit IR signals provided by request body.

        Args:
            message: JSON serialized object describing infrared signals.
              Includes "data", "freq" and "format" keys.
        """
        endpoint = "/messages"
        resp = await self.__request(endpoint, HTTPMethod.POST, message)
        if not resp.ok:
            raise NatureRemoError(f"{resp.status_code} {resp.reason}")
