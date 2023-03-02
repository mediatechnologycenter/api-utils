#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import multiprocessing
from typing import Union

import debugpy


def initialize_api_debugger(debug_port: Union[int, str]):
    if multiprocessing.current_process().pid > 1:
        if debug_port is None:
            raise RuntimeError("debug_port is None")

        debug_port = int(debug_port)
        debugpy.listen(("0.0.0.0", debug_port))
        print("⏳ Debugging server is running on port {}. VS Code debugger can now be attached, press F5 in VS Code ⏳".format(debug_port), flush=True)
        debugpy.wait_for_client()
        print("🎉 VS Code debugger attached, enjoy debugging 🎉", flush=True)
