#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

from unittest import TestCase

from starlette.testclient import TestClient

from mtc_api_utils.api import BaseApi
from mtc_api_utils.clients.api_client import ApiClient
from mtc_api_utils.tests.config import TestConfig

test_api = BaseApi(is_ready=lambda: True, config=TestConfig)


class TestIntegrationTest(TestCase):
    client = ApiClient(backend_url="", http_client=TestClient(test_api))

    def test_integration_test(self):
        resp, liveness = self.client.get_liveness()
        self.assertTrue(liveness)

        resp, readiness = self.client.get_readiness()
        self.assertTrue(readiness)

        resp, status = self.client.get_status()
        self.assertTrue(status.readiness)
