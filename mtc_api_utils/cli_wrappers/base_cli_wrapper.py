#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details


import subprocess
from enum import Enum
from typing import List


class Executable(Enum):
    value: str
    git = "git"
    helm = "helm"
    kubectl = "kubectl"


class CLIWrapperException(Exception):
    """
    Exception raised by an MTC CLIWrapper
    """

    @property
    def error(self) -> str:
        return str(self)


class BaseCLIWrapper:

    @classmethod
    def _run_command(cls, executable: Executable, args: List[str], working_dir: str = None) -> subprocess.CompletedProcess:
        full_args = [
            executable.value,
            *args,
        ]

        # print(f"Running the following command: {' '.join(full_args)}")  # DEBUG log
        try:
            completed_process = subprocess.run(
                args=full_args,
                check=True,
                cwd=working_dir,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise CLIWrapperException(e.stderr.decode("utf-8"))

        return completed_process
