#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import shutil
import unittest

from mtc_api_utils.cli_wrappers.git_wrapper import GitWrapper

test_repo_base_path = "/tmp/tests/gitRepos"
test_release_name = "test-release-name"
test_repo_url = "git@gitlab.ethz.ch:mtc/internal-projects/example-project.git"
test_branch = "main"
test_chart_path = "helm-test-chart"

test_namespace = "tests"


class TestHelmClientWrapper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        client = GitWrapper(repo_base_path=test_repo_base_path)
        cls.client = client

    def test_clone_or_pull_repository(self):
        # Remove existing repository
        shutil.rmtree(test_repo_base_path, ignore_errors=True)

        # Clone new repository
        self.client.clone_or_pull_repository(
            repo_url=test_repo_url,
            branch=test_branch,
        )

        # Pull existing repository
        self.client.clone_or_pull_repository(
            repo_url=test_repo_url,
            branch=test_branch,
        )

    def test_get_commit_hash(self):
        repo_url = self.client.get_full_repo_path(test_repo_url)
        short_hash = self.client.get_commit_hash(full_repo_path=repo_url)
        self.assertEqual(7, len(short_hash), msg=f"Expected short_hash: {short_hash} to have a length of 7")

    def test_commit_date(self):
        repo_url = self.client.get_full_repo_path(test_repo_url)

        try:
            date = self.client.get_commit_date(full_repo_path=repo_url)
            print(f"Commit date: {date.isoformat()=}")
        except Exception as err:
            self.fail(f"Unable to parse commit date: {err}")
