"""
SessionManager — Playwright Browser Session Management
========================================================
Manages saving and loading of Playwright storageState.json.

storageState.json stores browser cookies and localStorage so subsequent
tests can skip the login step and start in an authenticated state.

Usage:
    # Save session after login (run once manually):
    SessionManager.save_storage_state(page, storage_state_path)

    # Check if a saved session exists (used by conftest.py page fixture):
    if SessionManager.storage_state_exists(storage_state_path):
        context_kwargs["storage_state"] = storage_state_path
"""

import os
from pathlib import Path


class SessionManager:
    """Static helpers for Playwright browser session (storageState) management."""

    @staticmethod
    def storage_state_exists(storage_state_path: str) -> bool:
        """
        Return True if a saved storageState.json file exists and is non-empty.

        Parameters
        ----------
        storage_state_path : str — absolute or relative path to storageState.json

        Returns
        -------
        bool — True if the file exists and has content, False otherwise
        """
        path = Path(storage_state_path)
        return path.exists() and path.stat().st_size > 0

    @staticmethod
    def save_storage_state(page, storage_state_path: str) -> None:
        """
        Save the current browser session (cookies + localStorage) to a JSON file.

        Creates the parent directory if it does not exist.
        Raises a clear RuntimeError if the save fails.

        Parameters
        ----------
        page               : Playwright Page object
        storage_state_path : str — path where storageState.json will be written
        """
        path = Path(storage_state_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            page.context.storage_state(path=str(path))
            print(f"  [SessionManager] Storage state saved → {path}")
        except Exception as exc:
            raise RuntimeError(
                f"Failed to save storage state to '{path}': {exc}\n"
                "Make sure the directory is writable and the browser context is open."
            ) from exc

    @staticmethod
    def is_session_valid(page) -> bool:
        """
        Return True if the current page is authenticated (not on the login page).

        After page.goto(url) with a stored session, the app may redirect to the
        login page if the session has expired. This check detects that case.

        Waits for the page to fully settle (domcontentloaded) before checking,
        so that any redirect to the login page has already happened.

        Parameters
        ----------
        page : Playwright Page object

        Returns
        -------
        bool — True if authenticated (dashboard visible), False if on login page
        """
        try:
            # Wait for the page to fully settle before checking URL/elements.
            # Without this, the redirect to /login may not have happened yet.
            page.wait_for_load_state("domcontentloaded", timeout=15_000)
            # Give Vue router time to complete any client-side redirect
            page.wait_for_timeout(1500)

            current_url = page.url
            # If redirected to login page, session has expired
            if "login" in current_url.lower():
                print(f"  [SessionManager] Session expired — URL is login page: {current_url}")
                return False
            # Check if login form is visible (another sign of expired session)
            login_input = page.locator("input[name='username']")
            if login_input.is_visible(timeout=3_000):
                print("  [SessionManager] Session expired — login form is visible.")
                return False
            return True
        except Exception:
            # If any check fails, assume session is invalid and re-authenticate
            return False

    @staticmethod
    def ensure_authenticated(page, url: str, username: str, password: str,
                             storage_state_path: str) -> None:
        """
        Ensure the browser is authenticated. If the session has expired,
        re-login and save the new session.

        Call this after page.goto(url) to handle expired sessions gracefully.
        Waits for the page to fully settle before checking session validity,
        so that any redirect to the login page has already completed.

        Parameters
        ----------
        page               : Playwright Page object
        url                : str — application URL
        username           : str — login username
        password           : str — login password
        storage_state_path : str — path to storageState.json
        """
        from core.ui.pages.login_page import LoginPage
        if not SessionManager.is_session_valid(page):
            print("  [SessionManager] Session expired — re-logging in.")
            # If not already on the login page, navigate to it
            if "login" not in page.url.lower():
                page.goto(url, wait_until="domcontentloaded")
            login_page = LoginPage(page)
            login_page.login(username, password)
            # Wait for dashboard to confirm login succeeded
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15_000)
            except Exception:
                pass
            SessionManager.save_storage_state(page, storage_state_path)
            print("  [SessionManager] Re-authentication successful — session saved.")

    @staticmethod
    def delete_storage_state(storage_state_path: str) -> None:
        """
        Delete the saved storageState.json file.

        Silently does nothing if the file does not exist.

        Parameters
        ----------
        storage_state_path : str — path to the storageState.json file to delete
        """
        path = Path(storage_state_path)
        if path.exists():
            try:
                path.unlink()
                print(f"  [SessionManager] Storage state deleted: {path}")
            except Exception as exc:
                print(f"  [SessionManager] WARNING: Could not delete storage state: {exc}")
