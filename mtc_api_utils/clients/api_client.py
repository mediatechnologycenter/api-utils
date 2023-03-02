#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details
import asyncio
import time
from asyncio import sleep
from datetime import datetime, timedelta
from enum import Enum
from http import HTTPStatus
from typing import Tuple, Optional, List, Dict

import httpx
from fastapi import HTTPException
from httpx import Client, Response, AsyncClient

from mtc_api_utils.api_types import ApiStatus


class ContentType(Enum):
    value: str
    JSON = "application/json"
    TEXT = "text/plain"


class ApiBaseRoutes(Enum):
    liveness = "/api/liveness"
    readiness = "/api/readiness"
    status = "/api/status"


class ApiClient:
    def __init__(self, backend_url: str, base_route_timeout_seconds: int = 2, http_client=Client(), async_client=AsyncClient()):
        self._backend_url = backend_url
        self._base_route_timeout_seconds = base_route_timeout_seconds
        self.http_client = http_client
        self.async_client = async_client

        self._liveness_route = backend_url + ApiBaseRoutes.liveness.value
        self._readiness_route = backend_url + ApiBaseRoutes.readiness.value
        self._status_route = backend_url + ApiBaseRoutes.status.value

    def get_liveness(self) -> Tuple[Optional[Response], bool]:
        """
        Asserts backend availability.

        Returns:
            response: the http response
            bool: true if liveness check successful
        """
        try:
            resp = self.http_client.get(url=self._liveness_route, timeout=self._base_route_timeout_seconds)
        except httpx.TransportError:
            return None, False

        return resp, resp.status_code == HTTPStatus.OK

    def get_readiness(self) -> Tuple[Optional[Response], bool]:
        """
        Asserts project readiness (Usually mostly reliant on model readiness).

        Returns:
            response: the http response
            bool: true if readiness check successful
        """
        try:
            resp = self.http_client.get(url=self._readiness_route, timeout=self._base_route_timeout_seconds)
        except httpx.TransportError as e:
            # print(f"An error occurred when requesting service readiness: {e}") # This is an expected error case and therefore does not have to be logged
            return None, False

        return resp, resp.status_code == HTTPStatus.OK

    def get_status(self) -> Tuple[Optional[Response], ApiStatus]:
        """
        Returns project Status as follows:
        \n - If the readiness key has a value of `false`, the project is running but not ready. This is most likely because some models are still initializing
        \n - The gpu_supported flag specifies if the service can make use of GPU resources
        \n - The gpu_supported flag specifies whether the current deployment is running with GPU resources enabled
        """
        try:
            resp = self.http_client.get(url=self._status_route, timeout=self._base_route_timeout_seconds)
        except httpx.TransportError:
            return None, ApiStatus(readiness=False, gpu_supported=False, gpu_enabled=False)

        resp.raise_for_status()

        status = ApiStatus.parse_obj(resp.json())

        return resp, status

    # TODO: Implement async wait -> minor API change
    def wait_for_service_readiness(self, timeout: timedelta = timedelta(minutes=3)) -> None:
        """
        Wait for a given service to be ready. This method should only ever be used in tests as it implements a busy wait.
        """
        start = datetime.now()
        err: Optional[Exception] = None

        while datetime.now() - start <= timeout:
            try:
                _, is_ready = self.get_readiness()
                if is_ready:
                    return
            except httpx.HTTPStatusError as err:
                pass

            time.sleep(3)

        message = f"Service did not become ready before timeout: {timeout}"
        if err is not None:
            message += f". The following exception was raised while waiting: {err}"

        raise HTTPException(detail=f"Service did not become ready before timeout: {timeout}", status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    async def wait_for_service_readiness_async(self, timeout: timedelta = timedelta(minutes=3)) -> None:
        start = datetime.now()
        err: Optional[Exception] = None

        while datetime.now() - start <= timeout:
            try:
                _, is_ready = self.get_readiness()
                if is_ready:
                    return
            except httpx.HTTPStatusError as err:
                pass

            await sleep(3)

        message = f"Service did not become ready before timeout: {timeout}"
        if err is not None:
            message += f". The following exception was raised while waiting: {err}"

        raise HTTPException(detail=f"Service did not become ready before timeout: {timeout}", status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    @staticmethod
    def get_headers(access_token: str = None, content_type: ContentType = None) -> dict:
        auth_header = {
            'Authorization': f'Bearer {access_token}',
        }

        if content_type:
            auth_header["Content-Type"]: content_type.value

        return auth_header

    async def parallel_get(
            self,
            urls: List[str],
            access_token: Optional[str] = None,
            follow_redirects: bool = False,
            raise_for_status: bool = False,
    ) -> Dict[str, Optional[Response]]:
        """ Gets all passed urls in parallel asynchronously. If a timeout occurs, the response will be None """

        url_map: Dict[str, Response] = {url: None for url in urls}

        await asyncio.gather(
            *[
                self._make_async_get_request(
                    url=url,
                    url_map=url_map,
                    access_token=access_token,
                    follow_redirects=follow_redirects,
                )
                for url in urls
            ],
            return_exceptions=True)

        if raise_for_status:
            for url, res in url_map.items():
                res.raise_for_status()

        return url_map

    async def _make_async_get_request(
            self,
            url: str,
            url_map: Dict[str, Response],
            access_token: Optional[str] = None,
            follow_redirects: bool = False
    ) -> None:
        resp = await self.async_client.get(
            url=url,
            headers=self.get_headers(access_token=access_token),
            follow_redirects=follow_redirects,
            timeout=self._base_route_timeout_seconds,
        )

        url_map[url] = resp
