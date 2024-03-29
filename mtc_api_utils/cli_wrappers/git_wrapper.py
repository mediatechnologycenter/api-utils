#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import os
import re
from datetime import datetime
from subprocess import CompletedProcess

from fastapi import HTTPException

from mtc_api_utils.cli_wrappers.base_cli_wrapper import BaseCLIWrapper, Executable


class GitWrapper(BaseCLIWrapper):

    def __init__(self, repo_base_path: str = "/tmp/gitRepos"):
        self.repo_base_path = repo_base_path

    def get_full_repo_path(self, repo_url) -> str:
        regex = re.search(r".*/([\d\w\-_]*)(?:\.git)?", repo_url)
        full_repo_path = os.path.join(self.repo_base_path, regex.group(1))
        return full_repo_path

    def clone_repository(self, repo_url: str, branch: str) -> CompletedProcess:
        try:
            os.makedirs(name=self.repo_base_path, exist_ok=True)
        except FileExistsError:
            pass

        # Clone repository
        try:
            return self._run_git_command(
                full_repo_path=self.repo_base_path,
                args=[
                    "clone",
                    "-b",
                    branch,
                    repo_url
                ],
            )
        except Exception as e:
            message = f"An unexpected error occurred when cloning the git repo: {repo_url} with branch {branch}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def pull_repository(self, full_repo_path: str) -> CompletedProcess:
        # Reset repo in case any other application made changes
        self._run_git_command(
            full_repo_path=full_repo_path,
            args=["reset", "--hard"],
        )

        # Pull branch
        try:
            return self._run_git_command(
                full_repo_path=full_repo_path,
                args=["pull", "--ff-only"],
            )
        except Exception as e:
            message = f"An unexpected error occurred when pulling the git repo: {full_repo_path}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def clone_or_pull_repository(self, repo_url: str, branch: str) -> bool:
        """
        If repository does not exist, clone repository and return False
        If repository already exists, pull repository and return True
        """
        try:
            os.makedirs(name=self.repo_base_path, exist_ok=True)
        except FileExistsError:
            pass

        full_repo_path = self.get_full_repo_path(repo_url)

        if os.path.isdir(full_repo_path):
            """Repo dir exists -> Pull repo"""
            self.pull_repository(full_repo_path=full_repo_path)

            return True

        else:
            """Repo dir does not exist -> Clone repo"""
            self.clone_repository(repo_url=repo_url, branch=branch)

            return False

    def get_commit_hash(self, full_repo_path: str) -> str:
        """Returns the short commit hash of the latest commit in the repository specified by the repo path"""

        try:
            process = self._run_git_command(full_repo_path=full_repo_path, args=["rev-parse", "--short", "HEAD"])
            return process.stdout.decode("utf-8").strip()
        except Exception as e:
            message = f"An unexpected error occurred when retrieving the commit hash: {full_repo_path}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def get_commit_date(self, full_repo_path: str) -> datetime:
        try:
            process = self._run_git_command(full_repo_path=full_repo_path, args=["show", "-s", "--format=%cI"])
            date_string = process.stdout.decode("utf-8").strip()
            return datetime.fromisoformat(date_string)
        except Exception as e:
            message = f"An unexpected error occurred when retrieving the commit date: {full_repo_path}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def _run_git_command(self, full_repo_path: str, args: list[str]) -> CompletedProcess:
        return self._run_command(
            executable=Executable.git,
            args=[
                "-C",
                full_repo_path,
                *args
            ]
        )
