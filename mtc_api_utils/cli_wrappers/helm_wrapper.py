#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import json
import os
from enum import Enum
from subprocess import CompletedProcess
from typing import List, Dict

from fastapi import HTTPException

from mtc_api_utils.cli_wrappers.base_cli_wrapper import BaseCLIWrapper, Executable, CLIWrapperException
from mtc_api_utils.cli_wrappers.git_wrapper import GitWrapper


class _InstallType(Enum):
    install = "install"
    upgrade = "update"
    install_or_update = "install_or_update"


class HelmClientWrapper(BaseCLIWrapper):

    def __init__(self, repo_base_path: str = "/tmp/gitRepos"):
        self.repo_base_path = repo_base_path
        self.git_client = GitWrapper(repo_base_path=repo_base_path)

    def install(
            self,
            repo_url: str,
            branch: str,
            release_name: str,
            chart_path: str,
            namespace: str = "default",
            values_override: Dict[str, str] = None,
    ):
        self._install_or_upgrade_internal(
            install_type=_InstallType.install,
            repo_url=repo_url,
            branch=branch,
            release_name=release_name,
            chart_path=chart_path,
            namespace=namespace,
            values_override=values_override,
        )

    def upgrade(
            self,
            repo_url: str,
            branch: str,
            release_name: str,
            chart_path: str,
            namespace: str = "default",
            values_override: Dict[str, str] = None,
    ):
        self._install_or_upgrade_internal(
            install_type=_InstallType.upgrade,
            repo_url=repo_url,
            branch=branch,
            release_name=release_name,
            chart_path=chart_path,
            namespace=namespace,
            values_override=values_override,
        )

    def install_or_upgrade(
            self,
            repo_url: str,
            branch: str,
            release_name: str,
            chart_path: str,
            namespace: str = "default",
            values_override: Dict[str, str] = None,
    ):
        self._install_or_upgrade_internal(
            install_type=_InstallType.install_or_update,
            repo_url=repo_url,
            branch=branch,
            release_name=release_name,
            chart_path=chart_path,
            namespace=namespace,
            values_override=values_override,
        )

    def _install_or_upgrade_internal(
            self,
            install_type: _InstallType,
            repo_url: str,
            branch: str,
            release_name: str,
            chart_path: str,
            namespace: str = "default",
            values_override: Dict[str, str] = None,
    ) -> None:

        full_chart_path = self._get_full_chart_path(repo_url=repo_url, chart_path=chart_path)

        self.git_client.clone_or_pull_repository(repo_url=repo_url, branch=branch)

        if not os.path.isdir(full_chart_path):
            raise CLIWrapperException(
                "Chart directory was not found, make sure the chart_path parameter is set correctly"
            )

        args = [
            "install" if install_type == _InstallType.install else "upgrade",
            "--install" if install_type == _InstallType.install_or_update else None,
            release_name,
            full_chart_path,
            "--namespace",
            namespace,
            *self._format_value_overrides(values_override),
        ]

        args = [arg for arg in args if arg is not None]

        try:
            self._run_command(executable=Executable.helm, args=args)
        except CLIWrapperException as e:
            message = f"An unexpected error occurred when {install_type.value}ing the helm chart with release name: {release_name} from repo: {repo_url} on branch {branch}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def remove(self, release_name: str, namespace: str = "default") -> None:
        args = [
            "uninstall",
            release_name,
            "--namespace",
            namespace,
        ]

        try:
            self._run_command(Executable.helm, args=args)
        except CLIWrapperException as e:
            message = f"An unexpected error occurred when removing the helm chart with release name: {release_name}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    def list(self, namespace: str = None) -> List[str]:
        """
        Returns a list of all helm releases.
        If namespace == None, returns releases from all namespaces, else only return releases from the specified namespace.
        """
        args = [
            "list",
            "--short",
            "--output",
            "json",
        ]

        if namespace:
            args.append("--namespace")
            args.append(namespace)
        else:
            args.append("--all-namespaces")

        try:
            process = self._run_command(Executable.helm, args=args)
        except CLIWrapperException as e:
            message = f"An unexpected error occurred when listing helm releases in namespace: {namespace}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

        try:
            return json.loads(process.stdout)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An exception occurred while parsing shell output as json: {process.stdout}: \n{e}")

    def get_project_deployment_status(self, release_name: str, namespace: str = "default") -> bool:
        args = [
            "get",
            "values",
            "--all",
            release_name,
            "--namespace",
            namespace,
        ]

        try:
            completed = self._run_command(Executable.helm, args=args)
            output = completed.stdout.decode("utf-8")
        except CLIWrapperException as e:
            if "Error: release: not found" in e.error:  # Project chart not installed -> not ready
                print(e)
                return False
            else:
                message = f"An exception occurred while getting values for helm chart: {release_name}"
                print(message)
                raise HTTPException(status_code=500, detail=message)

        if "deployProject: true" in output:
            return True

        elif "deployProject: false" in output:
            return False

        print(f"stdout: {output}")
        raise CLIWrapperException("Expected values.deployment.deployProject to be either true or false")

    def build_chart_dependencies(self, full_chart_path: str) -> CompletedProcess:
        try:
            return self._run_command(
                executable=Executable.helm,
                args=[
                    "dependency",
                    "update",
                ],
                working_dir=full_chart_path
            )
        except CLIWrapperException as e:
            message = f"An unexpected error occurred while building chart dependencies for {full_chart_path}: \n{e}"
            print(message)
            raise HTTPException(status_code=500, detail=message)

    @classmethod
    def _run_helm_command(cls, namespace: str, args: List[str], value_overrides: Dict[str, str], working_dir: str = None) -> CompletedProcess:
        return cls._run_command(
            executable=Executable.helm,
            args=[
                *args,
                "--namespace",
                namespace,
                *cls._format_value_overrides(value_overrides),
            ],
            working_dir=working_dir,
        )

    def _get_full_chart_path(self, repo_url: str, chart_path: str) -> str:
        return os.path.join(self.git_client.get_full_repo_path(repo_url=repo_url), chart_path)

    @staticmethod
    def _format_value_overrides(values_override: Dict[str, str]) -> List[str]:
        values: List[str] = []
        for name, value in values_override.items():
            values.append("--set")
            values.append(f"{name}={value}")

        return values
