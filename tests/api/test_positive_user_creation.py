"""
test_positive_user_creation.py — Data-Driven API Tests: User CRUD
===================================================================
Covers:
  TC-API-001  POST /user with valid data → 200 OK + full body validation
  TC-API-003  GET  /user/{username} → 200 + full body validation
  TC-API-004  PUT  /user/{username} → 200 + follow-up GET verification
  TC-API-005  DELETE /user/{username} → 200 + follow-up GET confirms 404
  TC-API-006  GET  /user/{username} non-existent → 404 + error body validation

Each test:
  1. Reads its own data from Excel inline (try/except fallback to defaults)
  2. Validates HTTP response status code — inline try/except + result()
  3. Validates response body structure (mandatory fields) — inline
  4. Validates response body field values and data types — inline
  5. Validates Content-Type header — inline
  6. Calls result("passed"/"failed", expected, actual) for every check

Test Data:
  testData/API_testData.xlsx → sheet: UserManagement
  Row identifiers:
    UserManagement_Create_User — user creation data

Actual Petstore API response structures (verified):
  POST /user  → {"code": 200, "type": "unknown", "message": "<user_id>"}
  PUT  /user  → {"code": 200, "type": "unknown", "message": "<user_id>"}
  DELETE /user → {"code": 200, "type": "unknown", "message": "<username>"}
  GET  /user  → {"id": int, "username": str, "firstName": str, "lastName": str,
                  "email": str, "password": str, "phone": str, "userStatus": int}
  GET  /user (404) → {"code": 1, "type": "error", "message": "User not found"}

Framework components:
  - api_client   create_user(), get_user(), update_user(), delete_user()
  - XLUtils      read_api_data_from_excel(), read_cloud_env()
  - result()     (core/common_modules.py) — used in EVERY assertion step
"""

import allure
import pytest

from core.utils.XLUtils import read_api_data_from_excel, read_cloud_env
from core.api.api_client import create_user, get_user, update_user, delete_user
from core.common_modules import result


@allure.feature("User Management API")
class TestUserManagement:
    """Data-driven API test suite — all data from testData/API_testData.xlsx."""

    # ── TC-API-001: POST /user ────────────────────────────────────────────────

    @allure.story("Create User")
    @allure.title("TC-API-001: POST /user — 200 OK + full body validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_positive_user_creation(self):
        """
        Verify POST /user returns 200 with full response body validation.

        Test Data: testData/API_testData.xlsx → UserManagement → UserManagement_Create_User
        Validates: status code, body structure, body values, Content-Type
        """
        cloud_env = read_cloud_env()

        # ── Arrange: read test data from Excel, fall back to defaults ─────────
        with allure.step("Read test data from API_testData.xlsx"):
            try:
                data = read_api_data_from_excel("UserManagement", "UserManagement_Create_User")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}

        if str(data.get("Flag", "")).strip() == "Yes":
            user_id    = int(data.get("id",         0))
            username   = str(data.get("username",   "xyz"))
            firstname  = str(data.get("firstname",  "xyz"))
            lastname   = str(data.get("lastname",   "xyz"))
            email      = str(data.get("email",      "xyz@test.com"))
            password   = str(data.get("password",   "xyz"))
            phone      = str(data.get("phone",      "1234567890"))
            userstatus = int(data.get("userstatus", 0))
        else:
            user_id, username, firstname, lastname = 0, "xyz", "xyz", "xyz"
            email, password, phone, userstatus = "xyz@test.com", "xyz", "1234567890", 0

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step(f"POST /user — username='{username}'"):
            response = create_user(
                cloud_env=cloud_env, id=user_id, username=username,
                firstname=firstname, lastname=lastname, email=email,
                password=password, phone=phone, userstatus=userstatus,
                tc="TC-API-001",
            )

        # ── Assert: Status Code ───────────────────────────────────────────────
        with allure.step("Verify HTTP status code is 200"):
            try:
                assert response.status_code == 200, (
                    f"Expected HTTP 200 but got {response.status_code}. Body: {response.text}"
                )
                result("passed",
                       "POST /user: Response status code should be 200",
                       f"Status code is {response.status_code}")
            except AssertionError as exc:
                result("failed",
                       "POST /user: Response status code should be 200",
                       str(exc))
                raise

        # ── Assert: Body Structure ────────────────────────────────────────────
        with allure.step("Verify response body has mandatory fields"):
            body = response.json()
            try:
                assert isinstance(body, dict), f"Body should be JSON object, got {type(body).__name__}"
                for field in ["code", "type", "message"]:
                    assert field in body, f"Body missing mandatory field '{field}'"
                result("passed",
                       "POST /user: Response body should contain ['code', 'type', 'message']",
                       f"All fields present: {list(body.keys())}")
            except AssertionError as exc:
                result("failed",
                       "POST /user: Response body structure check failed",
                       str(exc))
                raise

        # ── Assert: Body Values ───────────────────────────────────────────────
        with allure.step("Verify response body field values"):
            try:
                assert body.get("code") == 200, \
                    f"body['code'] should be 200, got {body.get('code')}"
                result("passed",
                       "POST /user: body['code'] should be 200",
                       f"body['code'] = {body.get('code')}")
            except AssertionError as exc:
                result("failed", "POST /user: body['code'] check failed", str(exc))
                raise

            try:
                assert isinstance(body.get("code"), int), "body['code'] must be an integer"
                assert isinstance(body.get("type"), str), "body['type'] must be a string"
                assert body.get("type") != "error", "body['type'] should not be 'error'"
                result("passed",
                       "POST /user: body['type'] should be a non-error string",
                       f"body['type'] = '{body.get('type')}'")
            except AssertionError as exc:
                result("failed", "POST /user: body['type'] check failed", str(exc))
                raise

            try:
                msg = body.get("message")
                assert msg is not None and str(msg).strip() != "", \
                    "body['message'] must not be None or empty"
                result("passed",
                       "POST /user: body['message'] should not be empty",
                       f"body['message'] = '{msg}'")
            except AssertionError as exc:
                result("failed", "POST /user: body['message'] check failed", str(exc))
                raise

        # ── Assert: Content-Type ──────────────────────────────────────────────
        with allure.step("Verify Content-Type header"):
            try:
                ct = response.headers.get("Content-Type", "")
                assert "application/json" in ct, f"Expected application/json, got '{ct}'"
                result("passed",
                       "POST /user: Content-Type should be application/json",
                       f"Content-Type = '{ct}'")
            except AssertionError as exc:
                result("failed",
                       "POST /user: Content-Type validation failed",
                       str(exc))
                raise

    # ── TC-API-003: GET /user/{username} ─────────────────────────────────────

    @allure.story("Get User")
    @allure.title("TC-API-003: GET /user/{username} — 200 OK + full body field validation")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_get_user_full_body_validation(self):
        """
        Verify GET /user/{username} returns 200 with full response body validation.

        Test Data: testData/API_testData.xlsx → UserManagement → UserManagement_Create_User
        Validates: status code, all 8 mandatory fields, data types, field values, Content-Type
        """
        cloud_env = read_cloud_env()

        # ── Arrange: read test data from Excel, fall back to defaults ─────────
        with allure.step("Read test data from API_testData.xlsx"):
            try:
                data = read_api_data_from_excel("UserManagement", "UserManagement_Create_User")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}

        if str(data.get("Flag", "")).strip() == "Yes":
            user_id    = int(data.get("id",         0))
            username   = str(data.get("username",   "xyz"))
            firstname  = str(data.get("firstname",  "xyz"))
            lastname   = str(data.get("lastname",   "xyz"))
            email      = str(data.get("email",      "xyz@test.com"))
            password   = str(data.get("password",   "xyz"))
            phone      = str(data.get("phone",      "1234567890"))
            userstatus = int(data.get("userstatus", 0))
        else:
            user_id, username, firstname, lastname = 0, "xyz", "xyz", "xyz"
            email, password, phone, userstatus = "xyz@test.com", "xyz", "1234567890", 0

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step(f"POST /user — create '{username}' before GET"):
            create_user(
                cloud_env=cloud_env, id=user_id, username=username,
                firstname=firstname, lastname=lastname, email=email,
                password=password, phone=phone, userstatus=userstatus,
                tc="TC-API-003-setup",
            )

        with allure.step(f"GET /user/{username}"):
            response = get_user(cloud_env=cloud_env, username=username, tc="TC-API-003")

        # ── Assert: Status Code ───────────────────────────────────────────────
        with allure.step("Verify HTTP status code is 200"):
            try:
                assert response.status_code == 200, (
                    f"Expected HTTP 200 but got {response.status_code}. Body: {response.text}"
                )
                result("passed",
                       f"GET /user/{username}: Response status code should be 200",
                       f"Status code is {response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Response status code should be 200",
                       str(exc))
                raise

        # ── Assert: Body Structure ────────────────────────────────────────────
        with allure.step("Verify response body has all 8 mandatory fields"):
            body = response.json()
            mandatory = ["id", "username", "firstName", "lastName", "email", "password", "phone", "userStatus"]
            try:
                assert isinstance(body, dict), f"Body should be JSON object, got {type(body).__name__}"
                for field in mandatory:
                    assert field in body, f"Body missing mandatory field '{field}'"
                result("passed",
                       f"GET /user/{username}: Response body should contain {mandatory}",
                       f"All fields present: {list(body.keys())}")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Response body structure check failed",
                       str(exc))
                raise

        # ── Assert: Data Types ────────────────────────────────────────────────
        with allure.step("Verify response body field data types"):
            try:
                assert isinstance(body["id"],         int),  "body['id'] must be int"
                assert isinstance(body["username"],   str),  "body['username'] must be str"
                assert isinstance(body["firstName"],  str),  "body['firstName'] must be str"
                assert isinstance(body["lastName"],   str),  "body['lastName'] must be str"
                assert isinstance(body["email"],      str),  "body['email'] must be str"
                assert isinstance(body["password"],   str),  "body['password'] must be str"
                assert isinstance(body["phone"],      str),  "body['phone'] must be str"
                assert isinstance(body["userStatus"], int),  "body['userStatus'] must be int"
                result("passed",
                       f"GET /user/{username}: All field data types should be correct",
                       "All data types validated")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Data type validation failed",
                       str(exc))
                raise

        # ── Assert: Field Values ──────────────────────────────────────────────
        with allure.step("Verify response body field values match request data"):
            try:
                assert body["id"] > 0, f"body['id'] must be positive, got {body['id']}"
                result("passed", f"GET /user/{username}: body['id'] should be positive",
                       f"body['id'] = {body['id']}")
            except AssertionError as exc:
                result("failed", f"GET /user/{username}: body['id'] check failed", str(exc))
                raise

            try:
                assert body["username"]  == username,  "username mismatch"
                assert body["firstName"] == firstname, "firstName mismatch"
                assert body["lastName"]  == lastname,  "lastName mismatch"
                assert body["email"]     == email,     "email mismatch"
                assert body["phone"]     == phone,     "phone mismatch"
                result("passed",
                       f"GET /user/{username}: All field values should match request data",
                       f"username='{body['username']}', email='{body['email']}'")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Field value mismatch",
                       str(exc))
                raise

            try:
                assert "@" in body["email"], f"email '{body['email']}' missing '@'"
                assert body["userStatus"] in (0, 1), f"userStatus must be 0 or 1"
                assert body["password"] is not None, "body['password'] must not be null"
                result("passed",
                       f"GET /user/{username}: Business rule validations passed",
                       "email has '@', userStatus in (0,1), password not null")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Business rule validation failed",
                       str(exc))
                raise

        # ── Assert: Content-Type ──────────────────────────────────────────────
        with allure.step("Verify Content-Type header"):
            try:
                ct = response.headers.get("Content-Type", "")
                assert "application/json" in ct, f"Expected application/json, got '{ct}'"
                result("passed",
                       f"GET /user/{username}: Content-Type should be application/json",
                       f"Content-Type = '{ct}'")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{username}: Content-Type validation failed",
                       str(exc))
                raise

    # ── TC-API-004: PUT /user/{username} ─────────────────────────────────────

    @allure.story("Update User")
    @allure.title("TC-API-004: PUT /user/{username} — 200 OK + follow-up GET verification")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_update_user(self):
        """
        Verify PUT /user/{username} returns 200 and updated data is reflected in GET.

        Test Data: testData/API_testData.xlsx → UserManagement → UserManagement_Create_User
        Validates: PUT status code, PUT body, follow-up GET reflects updated values
        """
        cloud_env = read_cloud_env()

        # ── Arrange: read test data from Excel, fall back to defaults ─────────
        with allure.step("Read test data from API_testData.xlsx"):
            try:
                data = read_api_data_from_excel("UserManagement", "UserManagement_Create_User")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}

        if str(data.get("Flag", "")).strip() == "Yes":
            user_id    = int(data.get("id",         0))
            username   = str(data.get("username",   "xyz"))
            firstname  = str(data.get("firstname",  "xyz"))
            lastname   = str(data.get("lastname",   "xyz"))
            email      = str(data.get("email",      "xyz@test.com"))
            password   = str(data.get("password",   "xyz"))
            phone      = str(data.get("phone",      "1234567890"))
            userstatus = int(data.get("userstatus", 0))
        else:
            user_id, username, firstname, lastname = 0, "xyz", "xyz", "xyz"
            email, password, phone, userstatus = "xyz@test.com", "xyz", "1234567890", 0

        updated_firstname = f"Updated_{firstname}"
        updated_email     = f"updated_{email}"

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step(f"POST /user — create '{username}' before update"):
            create_user(
                cloud_env=cloud_env, id=user_id, username=username,
                firstname=firstname, lastname=lastname, email=email,
                password=password, phone=phone, userstatus=userstatus,
                tc="TC-API-004-setup",
            )

        with allure.step(f"PUT /user/{username} — update firstName and email"):
            response = update_user(
                cloud_env=cloud_env, id=user_id, username=username,
                firstname=updated_firstname, lastname=lastname,
                email=updated_email, password=password,
                phone=phone, userstatus=userstatus,
                tc="TC-API-004",
            )

        # ── Assert: PUT Status Code ───────────────────────────────────────────
        with allure.step("Verify PUT HTTP status code is 200"):
            try:
                assert response.status_code == 200, (
                    f"Expected HTTP 200 but got {response.status_code}. Body: {response.text}"
                )
                result("passed",
                       f"PUT /user/{username}: Response status code should be 200",
                       f"Status code is {response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"PUT /user/{username}: Response status code should be 200",
                       str(exc))
                raise

        # ── Assert: PUT Body ──────────────────────────────────────────────────
        with allure.step("Verify PUT response body"):
            body = response.json()
            try:
                assert isinstance(body, dict), f"Body should be JSON object, got {type(body).__name__}"
                for field in ["code", "type", "message"]:
                    assert field in body, f"Body missing mandatory field '{field}'"
                result("passed",
                       f"PUT /user/{username}: Response body should contain ['code', 'type', 'message']",
                       f"All fields present: {list(body.keys())}")
            except AssertionError as exc:
                result("failed",
                       f"PUT /user/{username}: Response body structure check failed",
                       str(exc))
                raise

            try:
                assert body.get("code") == 200, \
                    f"body['code'] should be 200, got {body.get('code')}"
                result("passed",
                       f"PUT /user/{username}: body['code'] should be 200",
                       f"body['code'] = {body.get('code')}")
            except AssertionError as exc:
                result("failed", f"PUT /user/{username}: body['code'] check failed", str(exc))
                raise

            try:
                assert isinstance(body.get("code"), int), "body['code'] must be an integer"
                assert isinstance(body.get("type"), str), "body['type'] must be a string"
                assert body.get("type") != "error", "body['type'] should not be 'error'"
                result("passed",
                       f"PUT /user/{username}: body['type'] should be a non-error string",
                       f"body['type'] = '{body.get('type')}'")
            except AssertionError as exc:
                result("failed", f"PUT /user/{username}: body['type'] check failed", str(exc))
                raise

            try:
                msg = body.get("message")
                assert msg is not None and str(msg).strip() != "", \
                    "body['message'] must not be None or empty"
                result("passed",
                       f"PUT /user/{username}: body['message'] should not be empty",
                       f"body['message'] = '{msg}'")
            except AssertionError as exc:
                result("failed", f"PUT /user/{username}: body['message'] check failed", str(exc))
                raise

        # ── Assert: Follow-up GET verifies update ─────────────────────────────
        with allure.step(f"GET /user/{username} — verify updated data"):
            get_response = get_user(cloud_env=cloud_env, username=username, tc="TC-API-004-verify")
            try:
                assert get_response.status_code == 200, (
                    f"Expected HTTP 200 but got {get_response.status_code}. Body: {get_response.text}"
                )
                result("passed",
                       f"Follow-up GET /user/{username}: Response status code should be 200",
                       f"Status code is {get_response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"Follow-up GET /user/{username}: Response status code should be 200",
                       str(exc))
                raise

            get_body = get_response.json()
            try:
                assert get_body.get("firstName") == updated_firstname, (
                    f"Expected firstName='{updated_firstname}' "
                    f"but got '{get_body.get('firstName')}'"
                )
                result("passed",
                       f"Follow-up GET: firstName should be '{updated_firstname}'",
                       f"firstName = '{get_body.get('firstName')}'")
            except AssertionError as exc:
                result("failed",
                       f"Follow-up GET: firstName should be '{updated_firstname}'",
                       str(exc))
                raise

            try:
                assert get_body.get("email") == updated_email, (
                    f"Expected email='{updated_email}' "
                    f"but got '{get_body.get('email')}'"
                )
                result("passed",
                       f"Follow-up GET: email should be '{updated_email}'",
                       f"email = '{get_body.get('email')}'")
            except AssertionError as exc:
                result("failed",
                       f"Follow-up GET: email should be '{updated_email}'",
                       str(exc))
                raise

    # ── TC-API-005: DELETE /user/{username} ──────────────────────────────────

    @allure.story("Delete User")
    @allure.title("TC-API-005: DELETE /user/{username} — 200 OK + follow-up GET confirms 404")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.api
    def test_delete_user(self):
        """
        Verify DELETE /user/{username} returns 200 and follow-up GET returns 404.

        Test Data: testData/API_testData.xlsx → UserManagement → UserManagement_Create_User
        Validates: DELETE status code, body message==username, follow-up GET 404
        """
        cloud_env = read_cloud_env()

        # ── Arrange: read test data from Excel, fall back to defaults ─────────
        with allure.step("Read test data from API_testData.xlsx"):
            try:
                data = read_api_data_from_excel("UserManagement", "UserManagement_Create_User")
            except Exception as exc:
                print(f"  [TestData] Excel row not found — using defaults. ({exc})")
                data = {}

        if str(data.get("Flag", "")).strip() == "Yes":
            user_id    = int(data.get("id",         0))
            username   = str(data.get("username",   "xyz"))
            firstname  = str(data.get("firstname",  "xyz"))
            lastname   = str(data.get("lastname",   "xyz"))
            email      = str(data.get("email",      "xyz@test.com"))
            password   = str(data.get("password",   "xyz"))
            phone      = str(data.get("phone",      "1234567890"))
            userstatus = int(data.get("userstatus", 0))
        else:
            user_id, username, firstname, lastname = 0, "xyz", "xyz", "xyz"
            email, password, phone, userstatus = "xyz@test.com", "xyz", "1234567890", 0

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step(f"POST /user — create '{username}' before delete"):
            create_user(
                cloud_env=cloud_env, id=user_id, username=username,
                firstname=firstname, lastname=lastname, email=email,
                password=password, phone=phone, userstatus=userstatus,
                tc="TC-API-005-setup",
            )

        with allure.step(f"DELETE /user/{username}"):
            response = delete_user(cloud_env=cloud_env, username=username, tc="TC-API-005")

        # ── Assert: DELETE Status Code ────────────────────────────────────────
        with allure.step("Verify DELETE HTTP status code is 200"):
            try:
                assert response.status_code == 200, (
                    f"Expected HTTP 200 but got {response.status_code}. Body: {response.text}"
                )
                result("passed",
                       f"DELETE /user/{username}: Response status code should be 200",
                       f"Status code is {response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"DELETE /user/{username}: Response status code should be 200",
                       str(exc))
                raise

        # ── Assert: DELETE Body ───────────────────────────────────────────────
        with allure.step("Verify DELETE response body"):
            body = response.json()
            try:
                assert isinstance(body, dict), f"Body should be JSON object, got {type(body).__name__}"
                for field in ["code", "type", "message"]:
                    assert field in body, f"Body missing mandatory field '{field}'"
                result("passed",
                       f"DELETE /user/{username}: Response body should contain ['code', 'type', 'message']",
                       f"All fields present: {list(body.keys())}")
            except AssertionError as exc:
                result("failed",
                       f"DELETE /user/{username}: Response body structure check failed",
                       str(exc))
                raise

            try:
                assert body["code"] == 200, f"body['code'] should be 200, got {body['code']}"
                result("passed",
                       f"DELETE /user/{username}: body['code'] should be 200",
                       f"body['code'] = {body['code']}")
            except AssertionError as exc:
                result("failed",
                       f"DELETE /user/{username}: body['code'] check failed",
                       str(exc))
                raise

            try:
                assert str(body["message"]) == username, (
                    f"body['message'] should be '{username}' (deleted username), "
                    f"got '{body['message']}'"
                )
                result("passed",
                       f"DELETE /user/{username}: body['message'] should be the deleted username",
                       f"body['message'] = '{body['message']}'")
            except AssertionError as exc:
                result("failed",
                       f"DELETE /user/{username}: body['message'] check failed",
                       str(exc))
                raise

        # ── Assert: Follow-up GET confirms 404 ───────────────────────────────
        with allure.step(f"GET /user/{username} — verify 404 after delete"):
            get_response = get_user(cloud_env=cloud_env, username=username, tc="TC-API-005-verify")
            try:
                assert get_response.status_code == 404, (
                    f"Expected HTTP 404 but got {get_response.status_code}. Body: {get_response.text}"
                )
                result("passed",
                       f"Follow-up GET /user/{username} after delete: Response status code should be 404",
                       f"Status code is {get_response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"Follow-up GET /user/{username} after delete: Response status code should be 404",
                       str(exc))
                raise

    # ── TC-API-006: GET /user/{username} non-existent → 404 ──────────────────

    @allure.story("Get User — Not Found")
    @allure.title("TC-API-006: GET /user/{username} non-existent — 404 + error body validation")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.api
    def test_get_nonexistent_user_returns_404(self):
        """
        Verify GET /user/{username} for a non-existent user returns 404.

        Test Data: No Excel data needed — uses hardcoded non-existent username.
        Validates: status code 404, body code=1, type='error', message='User not found'
        """
        cloud_env        = read_cloud_env()
        nonexistent_user = "ZZZNONEXISTENTUSER99999"

        # ── Act ───────────────────────────────────────────────────────────────
        with allure.step(f"GET /user/{nonexistent_user} — expect 404"):
            response = get_user(cloud_env=cloud_env, username=nonexistent_user, tc="TC-API-006")

        # ── Assert: Status Code ───────────────────────────────────────────────
        with allure.step("Verify HTTP status code is 404"):
            try:
                assert response.status_code == 404, (
                    f"Expected HTTP 404 but got {response.status_code}. Body: {response.text}"
                )
                result("passed",
                       f"GET /user/{nonexistent_user}: Response status code should be 404",
                       f"Status code is {response.status_code}")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{nonexistent_user}: Response status code should be 404",
                       str(exc))
                raise

        # ── Assert: Body Structure ────────────────────────────────────────────
        with allure.step("Verify 404 response body has mandatory fields"):
            body = response.json()
            try:
                assert isinstance(body, dict), f"Body should be JSON object, got {type(body).__name__}"
                for field in ["code", "type", "message"]:
                    assert field in body, f"Body missing mandatory field '{field}'"
                result("passed",
                       f"GET /user/{nonexistent_user} 404: Response body should contain ['code', 'type', 'message']",
                       f"All fields present: {list(body.keys())}")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{nonexistent_user} 404: Response body structure check failed",
                       str(exc))
                raise

        # ── Assert: Body Values ───────────────────────────────────────────────
        with allure.step("Verify 404 response body field values"):
            try:
                assert body["code"] == 1, f"Expected error code=1 but got {body['code']}"
                assert isinstance(body["code"], int), "body['code'] must be int"
                result("passed",
                       "GET /user 404: body['code'] should be 1",
                       f"body['code'] = {body['code']}")
            except AssertionError as exc:
                result("failed",
                       "GET /user 404: body['code'] check failed",
                       str(exc))
                raise

            try:
                assert body["type"] == "error", \
                    f"Expected type='error' but got '{body['type']}'"
                assert isinstance(body["type"], str), "body['type'] must be str"
                result("passed",
                       "GET /user 404: body['type'] should be 'error'",
                       f"body['type'] = '{body['type']}'")
            except AssertionError as exc:
                result("failed",
                       "GET /user 404: body['type'] check failed",
                       str(exc))
                raise

            try:
                assert body["message"] == "User not found", (
                    f"Expected 'User not found' but got '{body['message']}'"
                )
                assert body["message"].strip() != "", "body['message'] must not be empty"
                result("passed",
                       "GET /user 404: body['message'] should be 'User not found'",
                       f"body['message'] = '{body['message']}'")
            except AssertionError as exc:
                result("failed",
                       "GET /user 404: body['message'] check failed",
                       str(exc))
                raise

        # ── Assert: Content-Type ──────────────────────────────────────────────
        with allure.step("Verify Content-Type header"):
            try:
                ct = response.headers.get("Content-Type", "")
                assert "application/json" in ct, f"Expected application/json, got '{ct}'"
                result("passed",
                       f"GET /user/{nonexistent_user} 404: Content-Type should be application/json",
                       f"Content-Type = '{ct}'")
            except AssertionError as exc:
                result("failed",
                       f"GET /user/{nonexistent_user} 404: Content-Type validation failed",
                       str(exc))
                raise
