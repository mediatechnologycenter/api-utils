#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

import unittest
from datetime import datetime, timedelta
from enum import Enum
from http import HTTPStatus
from multiprocessing import Process
from time import sleep
from typing import Dict, Tuple, Optional, Any

import uvicorn
from fastapi import HTTPException, Depends
from firebase_admin.auth import UserNotFoundError
from httpx import HTTPStatusError, Response, post, get
from pydantic import BaseModel

from mtc_api_utils.api import BaseApi, service_unavailable_exception
from mtc_api_utils.api_types import FirebaseUser
from mtc_api_utils.assertions import assert_resp_raises
from mtc_api_utils.clients.api_client import ApiClient
from mtc_api_utils.clients.firebase_client import firebase_user_auth
from mtc_api_utils.tests.config import TestConfig
from mtc_api_utils.tests.test_firebase_client import firebase_client


class TestEnum(Enum):
    DE = "de"
    EN = "en"
    FR = "fr"


class TestRequest(BaseModel):
    message: str
    enum_field: Optional[TestEnum]
    optional_field: Optional[Any]


# Identical to TestRequest but separate to simulate more accurately
class TestResponse(TestRequest):
    pass


class TestBaseApi(unittest.TestCase):
    """
    Tests BaseApi and ApiClient classes
    """

    BACKEND_HOST = "http://localhost"
    BACKEND_PORT = "5555"

    BACKEND_URL = f"{BACKEND_HOST}:{BACKEND_PORT}"

    TEST_FIREBASE_PROJECT_ID = "mtc-dev"

    def tearDown(self) -> None:
        sleep(1)  # Required to properly shut down test servers & free ports

    def test_run_api(self):
        self.skipTest("Skipping test because it does not terminate when run automatically. Use manually when developing BaseApi")

        def is_ready() -> bool:
            return False

        api = BaseApi(is_ready=is_ready, config=TestConfig)

        user_auth = firebase_user_auth(config=TestConfig)

        @api.get(
            "/unauthenticated",
            response_model=TestResponse,
            tags=["Auth routes"],
        )
        async def unauthenticated_route():
            return TestResponse(message="Success!", enum_field=TestEnum.DE)

        @api.get(
            "/authenticated",
            response_model=TestResponse,
            tags=["Auth routes"],
        )
        async def authenticated_route(firebase_user=Depends(user_auth.with_roles(["admin"]))):
            print(f"Checking user authentication")

            self.assertIsNotNone(firebase_user)

            return TestResponse(message="Successfully authenticated!")

        uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT))

    def test_create_base_api(self):
        api = BaseApi(is_ready=lambda: True, config=TestConfig)

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            # Run Tests
            client = ApiClient(self.BACKEND_URL)

            # Test liveness
            resp, success = client.get_liveness()
            self.assertTrue(success)
            self.assertEqual(resp.status_code, HTTPStatus.OK)

            # Test readiness
            resp, success = client.get_readiness()
            self.assertTrue(success)
            self.assertEqual(resp.status_code, HTTPStatus.OK)
            self.assertIn("True", resp.text)

            # Test status
            resp, status = client.get_status()
            self.assertTrue(status.readiness)
            self.assertTrue(status.gpu_supported)
            # self.assertFalse(status.gpu_enabled)

        finally:
            api_process.terminate()

    def test_create_model_api(self):
        test_body = {"test": "ok"}
        test_inference_route = "/api/inference"

        start_time = datetime.now()
        api = BaseApi(is_ready=lambda: datetime.now() - start_time > timedelta(seconds=2), config=TestConfig)

        @api.post(test_inference_route)
        def inference_method(body: dict):
            """
                Checks if parsed body is as expected
            """

            if body == test_body:
                return "Inference successful"

            raise HTTPException(detail=f"Expected the following body: {test_body}", status_code=HTTPStatus.BAD_REQUEST)

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            # Create test client
            class ModelClient(ApiClient):

                @staticmethod
                def post_inference(body: Dict) -> Tuple[Response, Dict]:
                    response = post(url=f"{self.BACKEND_URL}{test_inference_route}", json=body)

                    response.raise_for_status()
                    return response, body

            # Run Tests
            client = ModelClient(self.BACKEND_URL)

            # Test liveness
            resp, success = client.get_liveness()
            self.assertTrue(success)
            self.assertEqual(resp.status_code, HTTPStatus.OK)

            # Test readiness
            resp, success = client.get_readiness()
            self.assertFalse(success)  # service_is_ready timeout should not yet be reached

            try:
                client.wait_for_service_readiness(timeout=timedelta(seconds=10))
            except HTTPException as e:
                self.fail(e.detail)

            # Test status
            resp, status = client.get_status()
            self.assertTrue(status.readiness)
            self.assertTrue(status.gpu_supported)  # Based on .env file
            # self.assertFalse(status.gpu_enabled)  # Based on .env file

            # Test inference route
            resp, test_body = client.post_inference(test_body)
            self.assertEqual(HTTPStatus.OK, resp.status_code)
            self.assertEqual(test_body, test_body)

        finally:
            api_process.terminate()

    def test_raise_api_exception(self):
        test_error_message = "Test error message"
        test_status_code = HTTPStatus.BAD_REQUEST

        start_time = datetime.now()
        api = BaseApi(is_ready=lambda: datetime.now() - start_time > timedelta(seconds=2), config=TestConfig)

        @api.get("/exception")
        def raise_exception():
            test_exception = HTTPException(detail=test_error_message, status_code=test_status_code)
            print(f"Raising exception: {test_exception}")
            raise test_exception

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            resp = get(url=f"{self.BACKEND_URL}/exception")
            assert_resp_raises(self, resp, service_unavailable_exception.detail, HTTPStatus.SERVICE_UNAVAILABLE)

            sleep(1)
            resp = get(url=f"{self.BACKEND_URL}/exception")
            assert_resp_raises(self, resp, test_error_message, test_status_code)

        finally:
            api_process.terminate()

    def test_serialization(self):
        test_message = "Success!"
        test_enum = TestEnum.DE

        test_serialization_route = "/test-serialization"
        api = BaseApi(is_ready=lambda: True, config=TestConfig)

        @api.get(
            test_serialization_route,
            response_model=TestResponse,
            response_model_exclude_none=True,
        )
        async def get_test_serialization():
            return TestResponse(message=test_message, enum_field=test_enum)

        @api.post(
            test_serialization_route,
            response_model=TestResponse,
            response_model_exclude_none=True,
        )
        async def post_test_serialization():
            return TestResponse(message=test_message, enum_field=test_enum)

        # Create test client
        class SerializationClient(ApiClient):
            @staticmethod
            def get_test_serialization() -> tuple[Response, TestResponse]:
                response = get(url=f"{self.BACKEND_URL}{test_serialization_route}")

                response.raise_for_status()

                response_body = TestResponse.parse_obj(response.json())
                return response, response_body

            @staticmethod
            def post_test_serialization(test_request: TestRequest) -> Tuple[Response, TestResponse]:
                response = post(
                    url=f"{self.BACKEND_URL}{test_serialization_route}",
                    json=test_request.json(),
                )

                response.raise_for_status()

                response_body = TestResponse.parse_obj(response.json())
                return response, response_body

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            client = SerializationClient(self.BACKEND_URL)

            # Test GET serialization
            resp, resp_body = client.get_test_serialization()

            raw_dict = resp.json()
            self.assertEqual(test_message, raw_dict["message"])
            self.assertEqual(test_enum.value, raw_dict["enum_field"])
            self.assertRaises(KeyError, lambda: raw_dict["optional_field"])

            # Deserialized & parsed Model
            self.assertEqual(test_message, resp_body.message)
            self.assertEqual(test_enum, resp_body.enum_field)
            self.assertEqual(None, resp_body.optional_field)

            # Test POST serialization
            request = TestRequest(
                message=test_message,
                enum_field=test_enum,
                optional_field=None,
            )

            resp, resp_body = client.post_test_serialization(request)

            raw_dict = resp.json()
            self.assertEqual(test_message, raw_dict["message"])
            self.assertEqual(test_enum.value, raw_dict["enum_field"])
            self.assertRaises(KeyError, lambda: raw_dict["optional_field"])

            # Deserialized & parsed Model
            self.assertEqual(test_message, resp_body.message)
            self.assertEqual(test_enum, resp_body.enum_field)
            self.assertEqual(None, resp_body.optional_field)

        finally:
            api_process.terminate()

    def test_firebase_bearer_authenticated_route(self):
        self.skipTest("Test cannot currently be executed as the service account lacks permission for some operations")

        test_email = "test@mtc-mail.ch"
        test_pw = "mtc-test-pw-321"
        test_role = "test"

        test_response_message = "Success!"

        api = BaseApi(is_ready=lambda: True, config=TestConfig)

        authenticated_user = firebase_user_auth(config=TestConfig)

        # Get or create test user & get access_token
        try:
            firebase_client.get_user(email=test_email)
        except UserNotFoundError:
            firebase_client.create_user(
                email=test_email,
                password=test_pw,
                roles=[test_role],
            )

        user_access_token = firebase_client.login_user(
            email=test_email,
            password=test_pw,
            firebase_project_api_key=TestConfig.firebase_test_project_key,
        )

        @api.get("/authenticated", response_model=TestResponse)
        async def authenticated_route(firebase_user: FirebaseUser = Depends(authenticated_user)):
            print(f"Checking user authentication")

            self.assertEqual(test_email, firebase_user.email)

            return TestResponse(message=test_response_message)

        @api.get(
            "/role-authenticated",
            response_model=TestResponse
        )
        def role_authenticated_route(firebase_user: FirebaseUser = Depends(authenticated_user.with_roles([test_role]))):
            print(f"Testing role authorization")

            self.assertEqual(test_email, firebase_user.email)
            self.assertEqual([test_role], firebase_user.roles)
            self.assertEqual(user_access_token, firebase_user.access_token)

            return TestResponse(message=test_response_message)

        @api.get(
            "/role-authenticated-failed",
            response_model=TestResponse,
            dependencies=[Depends(authenticated_user.with_roles(["user_does_not_have_this_role"]))],
        )
        def role_authenticated_route_not_authenticated():
            self.fail("User should not have been successfully authorized, because he does not have the required role")

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            authenticated_route = f"{self.BACKEND_URL}/authenticated"
            role_authenticated_route = f"{self.BACKEND_URL}/role-authenticated"
            role_authenticated_route_not_authorized = f"{self.BACKEND_URL}/role-authenticated-failed"

            # Unauthenticated request
            resp = get(url=authenticated_route)
            assert_resp_raises(self, resp, status_code=HTTPStatus.FORBIDDEN)

            try:
                # Authenticated request
                resp = get(
                    url=authenticated_route,
                    headers=ApiClient.get_headers(access_token=user_access_token),
                )

                resp.raise_for_status()
                self.assertIn(test_response_message, resp.text)

                # Authorized request
                user_record = {
                    test_role: True,
                    "some_other_key": "some_other_value",
                }

                # Assert client functionality
                roles = firebase_client.get_user_roles(user_record)
                self.assertListEqual([test_role], roles)

                # Assert end to end functionality
                resp = get(
                    url=role_authenticated_route,
                    headers=ApiClient.get_headers(access_token=user_access_token),
                )

                resp.raise_for_status()
                self.assertIn(test_response_message, resp.text)

                # Unauthorized request
                resp = get(
                    url=role_authenticated_route_not_authorized,
                    headers=ApiClient.get_headers(access_token=user_access_token),
                )
                assert_resp_raises(self, resp, status_code=HTTPStatus.FORBIDDEN, expected_exception=HTTPStatusError)

            finally:
                user = firebase_client.get_user(email=test_email)
                firebase_client.delete_user(user.uid)

        finally:
            api_process.terminate()

    def test_disable_firebase_bearer_authentication(self):
        class AuthDisabledConfig(TestConfig):
            auth_enabled = False

        api = BaseApi(is_ready=lambda: True, config=AuthDisabledConfig)

        # Create a firebase client, but disable auth
        authenticated_user = firebase_user_auth(config=AuthDisabledConfig)

        @api.get(
            "/authenticated",
            response_model=TestResponse,
            dependencies=[Depends(authenticated_user.with_roles(["auth_disabled"]))],
        )
        def authenticated_route():
            print(f"Checking user authentication")

            return TestResponse(message="Successfully disabled firebase auth")

        api_process = Process(target=lambda: uvicorn.run(api, host='0.0.0.0', port=int(self.BACKEND_PORT)))
        api_process.start()
        sleep(1)

        try:
            authenticated_route = f"{self.BACKEND_URL}/authenticated"

            # Unauthenticated request
            resp = get(url=authenticated_route)

            try:
                resp.raise_for_status()
            except Exception as e:
                self.fail(e)

        finally:
            api_process.terminate()
