import unittest
from http import HTTPStatus

from httpx import HTTPStatusError

from mtc_api_utils.clients.api_client import ApiClient


class TestApiClient(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = ApiClient(backend_url="https://github.com")

    async def test_parallel_get(self):
        test_urls = {
            "https://github.com/mediatechnologycenter": HTTPStatus.OK,
            "https://github.com/masus04": HTTPStatus.OK,
            "https://github.com/This/Path/Should/Not/Exist": HTTPStatus.NOT_FOUND,
        }

        responses = await self.client.parallel_get(urls=list(test_urls.keys()))
        for path, resp in responses.items():
            self.assertEqual(test_urls[path], resp.status_code, msg=f"{path=}")

        try:
            await self.client.parallel_get(urls=list(test_urls.keys()), raise_for_status=True)
            self.fail(msg="Expected request to fail with 404 NOT FOUND")
        except HTTPStatusError as e:
            self.assertEqual(HTTPStatus.NOT_FOUND, e.response.status_code)
