#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

from slack_sdk import WebClient
from slack_sdk.web import SlackResponse


class SlackClient:

    def __init__(self, channel: str, token: str):
        self.channel = channel
        self.token = token
        self.slack_client = WebClient(token=token)

    def post_message(self, title: str, message: str) -> SlackResponse:
        response = self.slack_client.chat_postMessage(
            channel=self.channel,
            text=message,
            mrkdwn=True,
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]
        )

        return response.validate()
