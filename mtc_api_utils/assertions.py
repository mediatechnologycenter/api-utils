#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import unittest
from typing import Type

from fastapi import HTTPException
from httpx import HTTPStatusError, Response

accepted_exceptions = [HTTPException]


# TODO: Add tests - This requires mocking of the requests.Response object, which does not seem to be trivial
def assert_resp_raises(
        test_case: unittest.TestCase,
        resp: Response,
        error_message: str = None,
        status_code: int = None,
        expected_exception: Type[Exception] = HTTPException
) -> None:
    """
    Asserts that a given response raises a certain exception.
    Special support for HTTPException, for which the message can also be asserted
    """

    if expected_exception not in accepted_exceptions and error_message:
        raise ValueError(f"assert_resp_raises only supports asserting error_message for expected_exception in {accepted_exceptions}")

    with test_case.assertRaises(HTTPStatusError) as cm:
        resp.raise_for_status()

    http_error = cm.exception

    if status_code:
        test_case.assertEqual(status_code, http_error.response.status_code)

    if expected_exception == HTTPException:
        test_case.assertEqual(status_code, resp.status_code)
        if error_message and resp.text:
            test_case.assertIn(error_message, resp.text)
