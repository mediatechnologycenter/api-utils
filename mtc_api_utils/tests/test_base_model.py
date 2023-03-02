#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import unittest
from time import sleep

from mtc_api_utils.base_model import MLBaseModel

test_message = "Success!"


class TestApiTypes(unittest.TestCase):

    def test_minimal_model(self):
        model_delay_seconds = 1

        class TestModel(MLBaseModel):
            def init_model(self):
                sleep(model_delay_seconds)

            def inference(self, *args, **kwargs) -> bool:
                return True

        model = TestModel()
        self.assertFalse(model.is_ready(), msg=f"Expected model to not be ready for {model_delay_seconds}s after initialization")

        sleep(model_delay_seconds * 1.5)
        self.assertTrue(model.is_ready(), msg=f"Expected model to be ready after initializing for {model_delay_seconds * 1.5}s after initialization")

    def test_ml_base_model(self):
        class TestModel(MLBaseModel):
            model = None

            def init_model(self):
                sleep(1)
                self.model = lambda: test_message

            def is_ready(self):
                return self.model is not None

            def inference(self, *args, **kwargs) -> str:
                return self.model()

        model = TestModel()

        self.assertFalse(model.is_ready(), msg="Expect model to be initializing")

        sleep(1.5)
        self.assertTrue(model.is_ready(), msg="Expect model to be done with initialization")
