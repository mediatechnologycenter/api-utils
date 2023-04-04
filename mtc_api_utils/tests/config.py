#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

from mtc_api_utils.config import Config


# DEPRECATED: This no longer works with the latest service account setup
class TestConfig(Config):
    slack_enabled: bool = Config.parse_env_var("SLACK_ENABLED", default="False", convert_type=bool)
    slack_token: str = Config.parse_env_var("SLACK_TOKEN")
    slack_channel: str = Config.parse_env_var("SLACK_CHANNEL")

    firebase_test_project_key: str = Config.parse_env_var(
        env_var_name="FIREBASE_TEST_PROJECT_KEY",
        default="",
    )

    firebase_test_admin_credentials_url: str = Config.parse_env_var(
        env_var_name="FIREBASE_TEST_ADMIN_CREDENTIALS_URL",
        default="https://www.polybox.ethz.ch/remote.php/dav/files/mtc_polybox/repo/credentials/dev-dashboard-admin-key.json",
    )
