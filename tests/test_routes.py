"""
Account API Service Test Suite
"""

import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

# EXERCISE 3
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  TEST CASES
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)

        # EXERCISE 5
        talisman.force_https = False

        init_db(app)

    def setUp(self):
        db.session.query(Account).delete()
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()

    ######################################################################
    # HELPER
    ######################################################################
    def _create_accounts(self, count):
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    # BASIC
    ######################################################################
    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    ######################################################################
    # SECURITY
    ######################################################################
    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': "default-src 'self'; object-src 'none'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }

        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    # 🔥 EXERCISE 7 (CORS TEST)
    def test_cors_security(self):
        """It should return a CORS header"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "*"
        )

    ######################################################################
    # CREATE
    ######################################################################
    def test_create_account(self):
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.get_json()
        self.assertEqual(data["name"], account.name)

    def test_bad_request(self):
        response = self.client.post(BASE_URL, json={"name": "bad"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="text/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    ######################################################################
    # READ
    ######################################################################
    def test_get_account(self):
        account = self._create_accounts(1)[0]
        response = self.client.get(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_account_not_found(self):
        response = self.client.get(f"{BASE_URL}/999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    # LIST
    ######################################################################
    def test_list_accounts(self):
        self._create_accounts(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    ######################################################################
    # UPDATE
    ######################################################################
    def test_update_account(self):
        account = self._create_accounts(1)[0]
        account.name = "Updated Name"

        response = self.client.put(
            f"{BASE_URL}/{account.id}",
            json=account.serialize(),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], "Updated Name")

    def test_update_account_not_found(self):
        response = self.client.put(
            f"{BASE_URL}/999",
            json={},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    # DELETE
    ######################################################################
    def test_delete_account(self):
        account = self._create_accounts(1)[0]
        response = self.client.delete(f"{BASE_URL}/{account.id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_account_not_found(self):
        response = self.client.delete(f"{BASE_URL}/999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    # ERROR
    ######################################################################
    def test_method_not_allowed(self):
        response = self.client.post(f"{BASE_URL}/1")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        