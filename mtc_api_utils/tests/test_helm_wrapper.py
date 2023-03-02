#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import shutil
import unittest

from mtc_api_utils.cli_wrappers.helm_wrapper import HelmClientWrapper, Executable, CLIWrapperException

test_repo_base_path = "/tmp/tests/gitRepos"
test_release_name = "test-release-name"
test_repo_url = "git@gitlab.ethz.ch:mtc/internal-projects/helm-client.git"  # TODO: Replace this with a new Test Project
test_branch = "main"
test_chart_path = "helm-test-chart"

test_namespace = "tests"


@unittest.skip("With the default implementation, the client is using a service account which does not have the required authorization to run this test")
class TestHelmClientWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        client = HelmClientWrapper(repo_base_path=test_repo_base_path)

        cls.client = client

        # Init test namespace
        try:
            client._run_command(
                Executable.kubectl,
                args=[
                    "create",
                    "namespace",
                    test_namespace,
                ],
            )
        except CLIWrapperException as e:
            if "already exists" not in e.error:
                raise e

    def test_clone_or_pull_repository(self):
        # Remove existing repository
        shutil.rmtree(test_repo_base_path, ignore_errors=True)

        # Init client

        # Clone new repository
        self.client.git_client.clone_or_pull_repository(
            repo_url=test_repo_url,
            branch=test_branch,
        )

        # Pull existing repository
        self.client.git_client.clone_or_pull_repository(
            repo_url=test_repo_url,
            branch=test_branch,
        )

    def test_install_upgrade_remove(self):
        # Cleanup
        try:
            self.remove()
        except Exception as e:
            """Most likely the release did not exist because it was properly cleaned up by a prior test"""

        # Run tests
        self.assertFalse(self.get_project_deployment_status())
        self.assertNotIn(test_release_name, self.list())

        self.install_or_upgrade(deploy_project=False)  # Install
        self.assertFalse(self.get_project_deployment_status())
        self.assertIn(test_release_name, self.list())

        self.install_or_upgrade(deploy_project=True)  # Upgrade
        self.assertTrue(self.get_project_deployment_status())
        self.assertIn(test_release_name, self.list())

        self.remove()
        self.assertFalse(self.get_project_deployment_status())
        self.assertNotIn(test_release_name, self.list())

    def install_or_upgrade(self, deploy_project: bool):
        self.client.install_or_upgrade(
            repo_url=test_repo_url,
            branch=test_branch,
            release_name=test_release_name,
            chart_path=test_chart_path,
            values_override={"deployment.deployProject": str(deploy_project)},
            namespace=test_namespace,
        )

    def remove(self):
        self.client.remove(
            release_name=test_release_name,
            namespace=test_namespace,
        )

    def list(self):
        return self.client.list()

    def get_project_deployment_status(self) -> bool:
        return self.client.get_project_deployment_status(
            release_name=test_release_name,
            namespace=test_namespace,
        )
