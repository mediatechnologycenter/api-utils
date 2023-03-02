#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import time
import unittest
from multiprocessing import Process

from mtc_api_utils.debug import initialize_api_debugger

DEBUG_PORT_INT = 5556
DEBUG_PORT_STR = "5557"
DEBUG_PORT_NONE = None


# Test cases
class TestDebug(unittest.TestCase):

    def test_start_debug_server(self):
        debug_process_int = Process(target=lambda: initialize_api_debugger(DEBUG_PORT_INT))
        debug_process_int.start()

        debug_process_str = Process(target=lambda: initialize_api_debugger(DEBUG_PORT_STR))
        debug_process_str.start()

        debug_process_none = Process(target=lambda: self.assertRaises(RuntimeError, initialize_api_debugger, DEBUG_PORT_NONE))
        debug_process_none.start()

        time.sleep(1)

        try:
            # Run Tests
            self.assertTrue(debug_process_str.is_alive())
            self.assertTrue(debug_process_int.is_alive())
            self.assertFalse(debug_process_none.is_alive())

        finally:
            debug_process_str.terminate()
            debug_process_int.terminate()
            debug_process_none.terminate()
