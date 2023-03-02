#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import enum
import os
import unittest
from typing import List

from mtc_api_utils.config import Config

# Test constants
test_debug = False
test_gpu = -1
test_backend_url = "http://localhost:5000"

default_value = "DEFAULT_VALUE"
no_default_value = "NO_DEFAULT_VALUE"

# Set env variables
os.environ[no_default_value] = no_default_value


# Test cases
class TestUnitConfig(unittest.TestCase):

    def test_init(self):
        class TestConfigClass(Config):
            debug: bool = Config.parse_env_var("DEBUG", default=str(test_debug), convert_type=bool)
            gpu: str = Config.parse_env_var("GPU", default=str(test_gpu))
            no_default_value = Config.parse_env_var(no_default_value)

        self.assertEqual(bool(test_debug), TestConfigClass.debug)
        self.assertEqual(str(test_gpu), TestConfigClass.gpu)
        self.assertEqual(no_default_value, TestConfigClass.no_default_value)

    def test_init_missing(self):
        class TestConfig(Config):
            pass

        self.assertRaises(ValueError, lambda: Config.parse_env_var("DEBUG"))

    def test_print_config(self):
        class TestConfigClass(Config):
            test_debug: bool = Config.parse_env_var("DEBUG", default=str(test_debug), convert_type=bool)
            test_gpu: str = Config.parse_env_var("GPU", default=str(test_gpu))
            no_default_value = Config.parse_env_var(no_default_value)

        TestConfigClass.print_config()

    def test_parse_env_var(self):
        class TestEnum(enum.Enum):
            TestEnum = "TestEnum"

        class TestConfig(Config):
            default_value: str = Config.parse_env_var(default_value, default=default_value)
            no_default_value: str = Config.parse_env_var(no_default_value)
            gpu: str = Config.parse_env_var("GPU", default=str(test_gpu))
            convert_type_gpu: str = Config.parse_env_var("GPU", default=str(test_gpu), convert_type=int)
            transform_gpu: int = Config.parse_env_var("GPU", default=str(test_gpu), transformation=lambda x: int(x))
            convert_enum: TestEnum = Config.parse_env_var(TestEnum.TestEnum.name, default=TestEnum.TestEnum.name, convert_type=TestEnum)
            convert_bool: bool = Config.parse_env_var("BOOL", default="True", convert_type=bool)
            convert_list: List[str] = Config.parse_env_var("LIST", default='this, is , a, list', convert_type=list)
            convert_list_second: List[str] = Config.parse_env_var("LIST", default='this,,carlo', convert_type=list)

        self.assertEqual(default_value, TestConfig.default_value)
        self.assertEqual(no_default_value, TestConfig.no_default_value)
        self.assertEqual(str(test_gpu), TestConfig.gpu)
        self.assertEqual(test_gpu, TestConfig.convert_type_gpu)
        self.assertEqual(test_gpu, TestConfig.transform_gpu)
        self.assertEqual(TestEnum.TestEnum, TestConfig.convert_enum)
        self.assertEqual(True, TestConfig.convert_bool)
        self.assertEqual(['this', 'is', 'a', 'list'], TestConfig.convert_list)
        self.assertEqual(['this', 'carlo'], TestConfig.convert_list_second)

        # Error cases
        self.assertRaises(ValueError, lambda: Config.parse_env_var(default_value))
        self.assertRaises(TypeError, lambda: Config.parse_env_var("GPU", default=test_gpu, convert_type=tuple))
        self.assertRaises(ZeroDivisionError, lambda: Config.parse_env_var("GPU", default=test_gpu, transformation=lambda x: 1 / 0))
        self.assertRaises(ValueError, lambda: Config.parse_env_var(TestEnum.TestEnum.name, default="NonexistantEnum", convert_type=TestEnum))
        self.assertRaises(ValueError, lambda: Config.parse_env_var("BOOL", default="f", convert_type=bool))
        self.assertRaises(ValueError, lambda: Config.parse_env_var("EMPTY"))
