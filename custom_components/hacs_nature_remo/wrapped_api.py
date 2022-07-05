from abc import ABC, abstractmethod

from remo import NatureRemoAPI as BaseAPI, NatureRemoError
from remo.api import HTTPMethod
from remo.errors import build_error_message
import requests


class SessionAPI(ABC):
    @property
    @abstractmethod
    def __response_type__(self):
        pass

    @abstractmethod
    def get(self, url, headers) -> __response_type__:
        NotImplementedError()

    @abstractmethod
    def post(self, url, headers, data) -> __response_type__:
        NotImplementedError()


class DefaultSessionAPI(SessionAPI):
    __response_type__ = requests.models.Response

    def get(self, url, headers):
        return requests.get(url, headers=headers)

    def post(self, url, headers, data):
        return requests.post(url, headers=headers, data=data)


class NatureRemoAPI(BaseAPI):
    def __init__(self, access_token: str, debug: bool = False, session: SessionAPI | None = None):
        super().__init__(access_token, debug)
        if session:
            self._session = session
        else:
            self._session = DefaultSessionAPI()

    def __request(
            self, endpoint: str, method: HTTPMethod, data: dict = None
    ) -> SessionAPI.__response_type__:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": f"nature-remo/hass",
        }
        url = f"{self.base_url}{endpoint}"

        try:
            if method == HTTPMethod.GET:
                return self._session.get(
                    url, headers=headers
                )
            else:
                return self._session.post(url, headers=headers, data=data)
        except OSError as e:
            raise NatureRemoError(e)

    def __get_json(self, resp: SessionAPI.__response_type__):
        self.__set_rate_limit(resp)
        if resp.ok:
            return resp.json()
        raise NatureRemoError(build_error_message(resp))
