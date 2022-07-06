from __future__ import annotations

import aiohttp

from . import HTTPWrapper, Response


class AioHttpWrapper(HTTPWrapper):

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__()
        self._session = session

    async def get(self, url, headers=None) -> Response:
        resp = await self._session.get(url=url, headers=headers)
        return _AioHttpResponseWrapper(resp)

    async def post(self, url, headers=None, data=None) -> Response:
        resp = await self._session.post(url=url, headers=headers, data=data)
        return _AioHttpResponseWrapper(resp)


class _AioHttpResponseWrapper(Response):
    def __init__(self, original: aiohttp.ClientResponse):
        super().__init__()
        self._original = original

    @property
    def ok(self):
        return self._original.ok

    @property
    def status_code(self) -> any:
        return self._original.status

    @property
    def headers(self):
        return self._original.headers

    # @headers.setter
    # def headers(self, data):
    #     pass

    @property
    def reason(self) -> str | None:
        return self._original.reason

    async def json(self):
        return await self._original.json()
