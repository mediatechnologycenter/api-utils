#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

# Test firebase client with test project
import unittest
from http import HTTPStatus
from os.path import isfile

from fastapi import HTTPException
from firebase_admin.auth import UserNotFoundError

from mtc_api_utils.clients.firebase_client import FirebaseClient
from mtc_api_utils.tests.config import TestConfig

TEST_EMAIL = "unittests@test.ch"
TEST_PW = "mtc-test-pw-321"
TEST_ROLE = "test"

FIREBASE_CREDENTIALS_FILENAME = "firebaseAdminCredentials.json"

firebase_client = FirebaseClient(config=TestConfig)


class TestFirebaseClientReadonly(unittest.TestCase):
    test_user_access_token: str

    def setUp(self) -> None:
        self.test_user_access_token = firebase_client.login_user(
            email=TEST_EMAIL,
            password=TEST_PW,
            firebase_project_api_key=TestConfig.firebase_test_project_key,
        )

    def get_user(self, expect_success=True):
        try:
            user = firebase_client.get_user(email=TEST_EMAIL)
            self.assertIsNotNone(user)
            return user

        except UserNotFoundError as e:
            if expect_success:
                self.fail(e)

    def test_validate_user(self):
        if TestConfig.firebase_auth_service_account_url == "":
            self.skipTest("Firebase disabled, cannot run test")

        # Assert valid user login successful
        try:
            firebase_client.verify_token(self.test_user_access_token)
        except Exception as e:
            self.fail(f"Valid token could not be verified: {e}")

        # Assert role validation
        try:
            user = firebase_client.get_user(TEST_EMAIL)
            # self.assertIn(TEST_ROLE, firebase_client.get_user_roles(user.custom_claims))
        except Exception as e:
            self.fail(f"Valid token could not be verified: {e}")

        # Assert invalid user login fails
        # Invalid token
        self.assertRaises(HTTPException, lambda: firebase_client.verify_token("invalid-token"))
        try:
            firebase_client.verify_token("invalid-token")
        except HTTPException as e:
            self.assertEqual(HTTPStatus.UNAUTHORIZED, e.status_code)

        # Expired token
        self.assertRaises(
            HTTPException,
            lambda: firebase_client.verify_token(
                "..eyJhbGciOiJSUzI1NiIsImtpZCI6ImYwNTM4MmFlMTgxYWJlNjFiOTYwYjA1Yzk3ZmE0MDljNDdhNDQ0ZTciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuL"
                "mdvb2dsZS5jb20vbXRjLWRldiIsImF1ZCI6Im10Yy1kZXYiLCJhdXRoX3RpbWUiOjE2MzQwNDA0MzksInVzZXJfaWQiOiJYcnJWeVFzaUZMU2FIR3ZZSFY0NUNkTjZrQU8yIiwic3ViIjo"
                "iWHJyVnlRc2lGTFNhSEd2WUhWNDVDZE42a0FPMiIsImlhdCI6MTYzNDA0MDQzOSwiZXhwIjoxNjM0MDQ0MDM5LCJlbWFpbCI6InRlc3RAbXRjLW1haWwuY2giLCJlbWFpbF92ZXJpZmllZ"
                "CI6ZmFsc2UsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZW1haWwiOlsidGVzdEBtdGMtbWFpbC5jaCJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.QRy2nIu6qNtpK8"
                "jPF0BT2oSreE7KNr5sj63AitcRPZMymOF5iVBefizunYujArHzM9oal6asG8rhK-EnEI4rDwSwcwcywOmDs_DfVlr6C2v2NXTh-jV1p8V3w0idhXUmus3gLxREVVu2RTUB1Wcd-FVdT-44"
                "DhiMLgsBKdwHAr6wsAFVNFFo52HbVH2G3UHoj4D5nKLXzFK5QfQ4etrRaXyrCQnlYocatJ-yqwL2zap6twqcgJbzijn-ycdV6XLaRsiJr1GxCpVFGQ_7s3Mk7_NQPOeCn81hwlc_dKAioI"
                "0vqD6J0e4bMNSZ1pmsuOH895VdWGXMq-AeJCDdvFcOEA"
            )
        )


@unittest.skip("The current authentication scheme only allows firebase service accounts to verify existing accounts (auth readonly)")
class TestFirebaseClient(unittest.TestCase):
    def setUp(self) -> None:
        # Delete test user if exists
        try:
            self.delete_user()
        except UserNotFoundError:
            pass

    def tearDown(self):
        self.setUp()

    def create_user(self):
        firebase_client.create_user(email=TEST_EMAIL, password=TEST_PW)
        self.delete_user()

        firebase_client.create_user(email=TEST_EMAIL, password=TEST_PW, roles=[TEST_ROLE])

    def update_user_roles(self):
        test_updated_user_roles = ["test", "updated"]

        user = firebase_client.get_user(email=TEST_EMAIL)
        firebase_client.update_user_roles(user.uid, roles=test_updated_user_roles)

        updated_user = firebase_client.get_user(email=TEST_EMAIL)
        updated_user_roles = firebase_client.get_user_roles(user=updated_user.custom_claims)

        self.assertEqual(test_updated_user_roles, updated_user_roles)

    @staticmethod
    def delete_user():
        user = firebase_client.get_user(TEST_EMAIL)
        firebase_client.delete_user(user_id=user.uid)

    def test_init_firebase_client(self):
        self.assertIsNotNone(firebase_client)

        self.assertTrue(isfile(FIREBASE_CREDENTIALS_FILENAME), f"{FIREBASE_CREDENTIALS_FILENAME} was not initialized to base directory")

    def test_create_get_delete_user(self):
        TestFirebaseClientReadonly().get_user(expect_success=False)
        self.create_user()

        TestFirebaseClientReadonly().get_user()
        self.update_user_roles()

        self.delete_user()
        TestFirebaseClientReadonly().get_user(expect_success=False)

    def test_list_users(self):
        users_page = firebase_client.list_users()
        self.assertGreaterEqual(len(users_page.users), 1)
        print(users_page)
