"""
AdminLocator — Element selectors for the Admin module.

Design principles:
  - Class-based string constants (consistent with PIMLocator, LoginLocator)
  - URL-based locators preferred over text-based (language-agnostic)
  - One canonical name per locator — no duplicate constants
  - All selectors verified against OrangeHRM OS 5.9
"""


class AdminLocator:
    """Static CSS / XPath selectors for the Admin → User Management module."""

    # ── Admin Module Navigation ───────────────────────────────────────────────
    ADMIN_MENU              = "//span[normalize-space()='Admin']"
    USER_MANAGEMENT_MENU    = "//span[normalize-space()='User Management']"
    USERS_SUBMENU           = "//a[normalize-space()='Users']"

    # ── System Users List Page ────────────────────────────────────────────────
    SYSTEM_USERS_TITLE      = "//h5[normalize-space()='System Users']"
    ADD_USER_BUTTON         = "//button[normalize-space()='Add']"
    USER_TABLE_ROWS         = "//div[@class='oxd-table-body']//div[@role='row']"
    NO_RECORDS_FOUND        = "//span[text()='No Records Found']"

    # ── Add User Form ─────────────────────────────────────────────────────────
    ADD_USER_TITLE          = "//h6[normalize-space()='Add User']"
    # User Role dropdown
    USER_ROLE_DROPDOWN      = "//label[text()='User Role']/following::div[@class='oxd-select-text-input'][1]"
    USER_ROLE_OPTION        = "//div[@role='listbox']//span[normalize-space()='{0}']"
    # Status dropdown
    STATUS_DROPDOWN         = "//label[text()='Status']/following::div[@class='oxd-select-text-input'][1]"
    STATUS_OPTION           = "//div[@role='listbox']//span[normalize-space()='{0}']"
    # Employee Name autocomplete
    EMPLOYEE_NAME_INPUT     = "//label[text()='Employee Name']/following::input[1]"
    AUTOCOMPLETE_OPTION     = "//div[contains(@class,'oxd-autocomplete-option')]"
    # Username and Password
    USERNAME_INPUT          = "//label[text()='Username']/following::input[1]"
    PASSWORD_INPUT          = "(//input[@type='password'])[1]"
    CONFIRM_PASSWORD_INPUT  = "(//input[@type='password'])[2]"
    # Save / Cancel
    SAVE_BUTTON             = "//button[normalize-space()='Save']"
    CANCEL_BUTTON           = "//button[normalize-space()='Cancel']"

    # ── Search Filters ────────────────────────────────────────────────────────
    SEARCH_USERNAME_INPUT   = "//label[text()='Username']/following::input[1]"
    SEARCH_BUTTON           = "//button[normalize-space()='Search']"
    RESET_BUTTON            = "//button[normalize-space()='Reset']"

    # ── Validation / Error Messages ───────────────────────────────────────────
    REQUIRED_ERROR          = "//span[text()='Required']"
    ALREADY_EXISTS_ERROR    = "//span[text()='Already exists']"
    PASSWORD_MISMATCH_ERROR = "//span[text()='Passwords do not match']"

    # ── Toast / Success Message ───────────────────────────────────────────────
    SUCCESS_TOAST           = "//div[contains(@class,'oxd-toast--success')]"
