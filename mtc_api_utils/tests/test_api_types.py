#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import unittest
from typing import Optional

from pydantic import Field

from mtc_api_utils.api_types import ApiType, ApiStatus, StandardTags

test_str = "test text"
test_int = 32


class TestApiTypes(unittest.TestCase):

    def test_api_type(self):
        class TestModel(ApiType):
            empty_val: Optional[str]
            str_val: str = Field(example="some test text")
            int_val: int = Field(example=3)

        test_model = TestModel(str_val=test_str, int_val=test_int)

        self.assertEqual(test_str, test_model.dict()["str_val"])
        self.assertEqual(test_int, test_model.dict()["int_val"])

    def test_inheritance(self):
        val1 = "val1"
        val2 = "val2"

        class BaseModel(ApiType):
            val1: str

        class ChildModel(BaseModel):
            val2: str

        dict_repr = {
            val1: val1,
            val2: val2,
        }

        base = BaseModel.parse_obj(dict_repr)
        child = ChildModel.parse_obj(dict_repr)

        self.assertEqual(val1, base.dict()[val1])
        self.assertEqual(val1, child.dict()[val1])
        self.assertEqual(val2, child.dict()[val2])

    def test_aliased_model(self):
        test_id = "test_id"

        class TestModel(ApiType):
            id: str = Field(alias="_id")

        model = TestModel(id=test_id)

        self.assertEqual(test_id, model.id)
        self.assertEqual(test_id, model.json_dict["_id"])

    def test_api_status(self):
        status = ApiStatus(
            readiness=True,
            gpu_supported=False,
            gpu_enabled=False,
        )

        self.assertTrue(status.readiness)
        self.assertFalse(status.gpu_supported)
        self.assertFalse(status.gpu_enabled)
        self.assertIn(StandardTags.demo.value, status.tags)
