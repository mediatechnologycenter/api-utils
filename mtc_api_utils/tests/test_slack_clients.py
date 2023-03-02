#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import unittest
from http import HTTPStatus

from mtc_api_utils.clients.slack_client import SlackClient
from mtc_api_utils.tests.config import TestConfig

test_text = "Test Text"
test_title = "Test Title"
test_emoji = ":robot_face:"


class TestApiTypes(unittest.TestCase):

    def test_slack_client(self):
        print(f"{TestConfig.slack_token=}")
        client = SlackClient(channel=TestConfig.slack_channel, token=TestConfig.slack_token)

        slack_resp = client.slack_client.api_test()
        self.assertEqual(HTTPStatus.OK, slack_resp.status_code)

    def test_slack_send_message(self):
        self.skipTest("Skipping in order to reduce channel spam")

        client = SlackClient(channel=TestConfig.slack_channel, token=TestConfig.slack_token)
        client.post_message(test_title, test_text)
