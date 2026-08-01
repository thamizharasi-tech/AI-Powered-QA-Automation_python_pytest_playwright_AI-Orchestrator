"""
api_client — HTTP Request Helpers
===================================
Provides pure functions for each REST API operation.
All test data is read from Excel via read_api_data_from_excel().
All responses are saved to file and Excel for traceability.

Design:
  - Pure functions (no `self` parameter)
  - Correct HTTP verbs: POST → create, PUT → update, GET → read, DELETE → delete
  - URL template substitution uses the correct pattern: .replace('{param}', value)
  - Explicit timeout on every request (default 30 s, override via E2E_API_TIMEOUT)
  - requests.exceptions.RequestException caught and re-raised with diagnostics
  - Persistence (file + Excel) attempted after every completed request
  - All helper logic (timeout, headers, payload parsing) handled inline per function
"""

import ast
import json
import os

import requests

from core.utils.XLUtils import read_api_data_from_excel, save_api_resp_in_excel
from core.e2e_testData import save_api_resp_into_file


# ─────────────────────────────────────────────────────────────────────────────
# POST — Create User
# ─────────────────────────────────────────────────────────────────────────────

def create_user(
    cloud_env: str,
    id: int,
    username: str,
    firstname: str,
    lastname: str,
    email: str,
    password: str,
    phone: str,
    userstatus: int,
    tc: str,
) -> requests.Response:
    """
    POST /user — Create a new user.

    Reads base URL, endpoint, headers, and payload template from Excel
    sheet "API_Data", row "create_user".

    Parameters
    ----------
    cloud_env   : str — environment name (used for logging only)
    id          : int — user ID
    username    : str — login username
    firstname   : str — first name
    lastname    : str — last name
    email       : str — email address
    password    : str — password
    phone       : str — phone number
    userstatus  : int — user status (0 = inactive, 1 = active)
    tc          : str — test case ID (used for logging only)

    Returns
    -------
    requests.Response

    Raises
    ------
    requests.exceptions.ConnectionError  — server unreachable
    requests.exceptions.Timeout          — request exceeded timeout
    requests.exceptions.RequestException — any other network error
    ValueError                           — malformed headers or payload in Excel
    """
    # ── Timeout ───────────────────────────────────────────────────────────────
    raw_timeout = os.environ.get("E2E_API_TIMEOUT", "30").strip()
    try:
        timeout = int(raw_timeout)
        timeout = timeout if timeout > 0 else 30
    except ValueError:
        timeout = 30

    # ── Read Excel data ───────────────────────────────────────────────────────
    data         = read_api_data_from_excel("API_Data", "create_user")
    complete_url = str(data["Base Url"]) + str(data["Endpoint"])

    # ── Parse headers ─────────────────────────────────────────────────────────
    try:
        headers = ast.literal_eval(str(data["Headers"]).replace("\n", ""))
    except (ValueError, SyntaxError) as exc:
        raise ValueError(
            f"Could not parse headers from Excel value: {data['Headers']!r}\n"
            f"Expected a Python dict literal, e.g. {{'Content-Type': 'application/json'}}\n"
            f"Original error: {exc}"
        ) from exc

    # ── Parse payload ─────────────────────────────────────────────────────────
    try:
        payload = json.loads(str(data["Payload"]).replace("\n", ""))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse payload from Excel value: {data['Payload']!r}\n"
            f"Expected valid JSON, e.g. {{\"id\": 0, \"username\": \"test\"}}\n"
            f"Original error: {exc}"
        ) from exc

    payload.update({
        "id":         id,
        "username":   username,
        "firstName":  firstname,
        "lastName":   lastname,
        "email":      email,
        "password":   password,
        "phone":      phone,
        "userStatus": userstatus,
    })
    payload.pop("firstname", None)
    payload.pop("lastname",  None)

    print(f"POST {complete_url}  [timeout={timeout}s]")
    print(f"Payload: {payload}")

    # ── HTTP request ──────────────────────────────────────────────────────────
    try:
        response = requests.post(
            complete_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"POST {complete_url} timed out after {timeout}s. "
            f"Check server availability or increase E2E_API_TIMEOUT."
        )
    except requests.exceptions.ConnectionError as exc:
        raise requests.exceptions.ConnectionError(
            f"POST {complete_url} — connection failed: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"POST {complete_url} — request failed: {exc}"
        ) from exc

    print(f"Response [{response.status_code}]: {response.text}")

    # ── Persist response ──────────────────────────────────────────────────────
    try:
        save_api_resp_into_file("create_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to file: {exc}")
    try:
        save_api_resp_in_excel("API_Data", "create_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to Excel: {exc}")

    return response


# ─────────────────────────────────────────────────────────────────────────────
# PUT — Update User
# ─────────────────────────────────────────────────────────────────────────────

def update_user(
    cloud_env: str,
    id: int,
    username: str,
    firstname: str,
    lastname: str,
    email: str,
    password: str,
    phone: str,
    userstatus: int,
    tc: str,
) -> requests.Response:
    """
    PUT /user/{username} — Update an existing user.

    Reads base URL, endpoint, headers, and payload template from Excel
    sheet "API_Data", row "update_user".

    Raises
    ------
    requests.exceptions.ConnectionError  — server unreachable
    requests.exceptions.Timeout          — request exceeded timeout
    requests.exceptions.RequestException — any other network error
    ValueError                           — malformed headers or payload in Excel
    """
    # ── Timeout ───────────────────────────────────────────────────────────────
    raw_timeout = os.environ.get("E2E_API_TIMEOUT", "30").strip()
    try:
        timeout = int(raw_timeout)
        timeout = timeout if timeout > 0 else 30
    except ValueError:
        timeout = 30

    # ── Read Excel data ───────────────────────────────────────────────────────
    data         = read_api_data_from_excel("API_Data", "update_user")
    complete_url = (str(data["Base Url"]) + str(data["Endpoint"])).replace(
        "{username}", username
    )

    # ── Parse headers ─────────────────────────────────────────────────────────
    try:
        headers = ast.literal_eval(str(data["Headers"]).replace("\n", ""))
    except (ValueError, SyntaxError) as exc:
        raise ValueError(
            f"Could not parse headers from Excel value: {data['Headers']!r}\n"
            f"Expected a Python dict literal, e.g. {{'Content-Type': 'application/json'}}\n"
            f"Original error: {exc}"
        ) from exc

    # ── Parse payload ─────────────────────────────────────────────────────────
    try:
        payload = json.loads(str(data["Payload"]).replace("\n", ""))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse payload from Excel value: {data['Payload']!r}\n"
            f"Expected valid JSON, e.g. {{\"id\": 0, \"username\": \"test\"}}\n"
            f"Original error: {exc}"
        ) from exc

    payload.update({
        "id":         id,
        "username":   username,
        "firstName":  firstname,
        "lastName":   lastname,
        "email":      email,
        "password":   password,
        "phone":      phone,
        "userStatus": userstatus,
    })
    payload.pop("firstname", None)
    payload.pop("lastname",  None)

    print(f"PUT {complete_url}  [timeout={timeout}s]")

    # ── HTTP request ──────────────────────────────────────────────────────────
    try:
        response = requests.put(
            complete_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"PUT {complete_url} timed out after {timeout}s. "
            f"Check server availability or increase E2E_API_TIMEOUT."
        )
    except requests.exceptions.ConnectionError as exc:
        raise requests.exceptions.ConnectionError(
            f"PUT {complete_url} — connection failed: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"PUT {complete_url} — request failed: {exc}"
        ) from exc

    print(f"Response [{response.status_code}]: {response.text}")

    # ── Persist response ──────────────────────────────────────────────────────
    try:
        save_api_resp_into_file("update_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to file: {exc}")
    try:
        save_api_resp_in_excel("API_Data", "update_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to Excel: {exc}")

    return response


# ─────────────────────────────────────────────────────────────────────────────
# GET — Read User
# ─────────────────────────────────────────────────────────────────────────────

def get_user(
    cloud_env: str,
    username: str,
    tc: str,
) -> requests.Response:
    """
    GET /user/{username} — Retrieve a user by username.

    Reads base URL, endpoint, and headers from Excel
    sheet "API_Data", row "get_user".

    Raises
    ------
    requests.exceptions.ConnectionError  — server unreachable
    requests.exceptions.Timeout          — request exceeded timeout
    requests.exceptions.RequestException — any other network error
    ValueError                           — malformed headers in Excel
    """
    # ── Timeout ───────────────────────────────────────────────────────────────
    raw_timeout = os.environ.get("E2E_API_TIMEOUT", "30").strip()
    try:
        timeout = int(raw_timeout)
        timeout = timeout if timeout > 0 else 30
    except ValueError:
        timeout = 30

    # ── Read Excel data ───────────────────────────────────────────────────────
    data         = read_api_data_from_excel("API_Data", "get_user")
    complete_url = (str(data["Base Url"]) + str(data["Endpoint"])).replace(
        "{username}", username
    )

    # ── Parse headers ─────────────────────────────────────────────────────────
    try:
        headers = ast.literal_eval(str(data["Headers"]).replace("\n", ""))
    except (ValueError, SyntaxError) as exc:
        raise ValueError(
            f"Could not parse headers from Excel value: {data['Headers']!r}\n"
            f"Expected a Python dict literal, e.g. {{'Content-Type': 'application/json'}}\n"
            f"Original error: {exc}"
        ) from exc

    print(f"GET {complete_url}  [timeout={timeout}s]")

    # ── HTTP request ──────────────────────────────────────────────────────────
    try:
        response = requests.get(
            complete_url,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"GET {complete_url} timed out after {timeout}s. "
            f"Check server availability or increase E2E_API_TIMEOUT."
        )
    except requests.exceptions.ConnectionError as exc:
        raise requests.exceptions.ConnectionError(
            f"GET {complete_url} — connection failed: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"GET {complete_url} — request failed: {exc}"
        ) from exc

    print(f"Response [{response.status_code}]: {response.text}")

    # ── Persist response ──────────────────────────────────────────────────────
    try:
        save_api_resp_into_file("get_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to file: {exc}")
    try:
        save_api_resp_in_excel("API_Data", "get_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to Excel: {exc}")

    return response


# ─────────────────────────────────────────────────────────────────────────────
# DELETE — Delete User
# ─────────────────────────────────────────────────────────────────────────────

def delete_user(
    cloud_env: str,
    username: str,
    tc: str,
) -> requests.Response:
    """
    DELETE /user/{username} — Delete a user by username.

    Reads base URL, endpoint, and headers from Excel
    sheet "API_Data", row "delete_user".

    Raises
    ------
    requests.exceptions.ConnectionError  — server unreachable
    requests.exceptions.Timeout          — request exceeded timeout
    requests.exceptions.RequestException — any other network error
    ValueError                           — malformed headers in Excel
    """
    # ── Timeout ───────────────────────────────────────────────────────────────
    raw_timeout = os.environ.get("E2E_API_TIMEOUT", "30").strip()
    try:
        timeout = int(raw_timeout)
        timeout = timeout if timeout > 0 else 30
    except ValueError:
        timeout = 30

    # ── Read Excel data ───────────────────────────────────────────────────────
    data         = read_api_data_from_excel("API_Data", "delete_user")
    complete_url = (str(data["Base Url"]) + str(data["Endpoint"])).replace(
        "{username}", username
    )

    # ── Parse headers ─────────────────────────────────────────────────────────
    try:
        headers = ast.literal_eval(str(data["Headers"]).replace("\n", ""))
    except (ValueError, SyntaxError) as exc:
        raise ValueError(
            f"Could not parse headers from Excel value: {data['Headers']!r}\n"
            f"Expected a Python dict literal, e.g. {{'Content-Type': 'application/json'}}\n"
            f"Original error: {exc}"
        ) from exc

    print(f"DELETE {complete_url}  [timeout={timeout}s]")

    # ── HTTP request ──────────────────────────────────────────────────────────
    try:
        response = requests.delete(
            complete_url,
            headers=headers,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        raise requests.exceptions.Timeout(
            f"DELETE {complete_url} timed out after {timeout}s. "
            f"Check server availability or increase E2E_API_TIMEOUT."
        )
    except requests.exceptions.ConnectionError as exc:
        raise requests.exceptions.ConnectionError(
            f"DELETE {complete_url} — connection failed: {exc}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"DELETE {complete_url} — request failed: {exc}"
        ) from exc

    print(f"Response [{response.status_code}]: {response.text}")

    # ── Persist response ──────────────────────────────────────────────────────
    try:
        save_api_resp_into_file("delete_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to file: {exc}")
    try:
        save_api_resp_in_excel("API_Data", "delete_user", response.text)
    except Exception as exc:
        print(f"  [api_client] WARNING: Could not save response to Excel: {exc}")

    return response
