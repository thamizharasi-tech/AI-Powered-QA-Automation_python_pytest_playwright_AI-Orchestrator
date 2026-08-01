"""
PIMLocator — Element selectors for the PIM module.

Design principles:
  - Class-based string constants (consistent with LoginLocator, DashboardLocator)
  - URL-based locators preferred over text-based (language-agnostic)
  - One canonical name per locator — no duplicate constants
  - All selectors verified against OrangeHRM OS 5.9
"""


class PIMLocator:
    """Static CSS / XPath selectors for the PIM module."""

    # ── PIM Module Header ─────────────────────────────────────────────────────
    PIM_HEADER                = "//h6[text()='PIM']"

    # ── Employee List Page ────────────────────────────────────────────────────
    # URL-based — language-agnostic (works regardless of OrangeHRM locale)
    EMPLOYEE_LIST_TITLE       = "//a[@href='/web/index.php/pim/viewPimModule' or contains(@href,'viewPimModule')]"
    EMPLOYEE_LIST_HEADER      = "//h5"
    ADD_EMPLOYEE_BUTTON       = "//button[normalize-space()='Add']"

    # ── Employee Search ───────────────────────────────────────────────────────
    # Label-following locators — placeholder 'Type for hints...' is ambiguous (2 inputs)
    EMPLOYEE_NAME_SEARCH      = "//label[text()='Employee Name']/following::input[1]"
    EMPLOYEE_ID_SEARCH        = "//label[text()='Employee Id']/following::input[1]"
    SEARCH_BUTTON             = "//button[normalize-space()='Search']"
    RESET_BUTTON              = "//button[normalize-space()='Reset']"
    EMPLOYEE_TABLE_ROWS       = "//div[@class='oxd-table-body']//div[@role='row']"
    EMPLOYEE_TABLE_FIRST_ROW  = "//div[@class='oxd-table-body']//div[@role='row'][1]"
    NO_RECORDS_FOUND          = "//span[text()='No Records Found']"

    # ── Add Employee Form ─────────────────────────────────────────────────────
    ADD_EMPLOYEE_TITLE        = "//h6[text()='Add Employee']"
    FIRST_NAME_INPUT          = "//input[@name='firstName']"
    MIDDLE_NAME_INPUT         = "//input[@name='middleName']"
    LAST_NAME_INPUT           = "//input[@name='lastName']"
    # Label-based locator — stable across Add Employee form and Personal Details page
    EMPLOYEE_ID_INPUT         = "//label[text()='Employee Id']/following::input[1]"
    CREATE_LOGIN_TOGGLE       = "//span[contains(@class,'oxd-switch-input')]"
    # Username input appears after enabling Create Login Details toggle
    USERNAME_INPUT            = "//label[text()='Username']/following::input[1]"
    STATUS_DROPDOWN           = "//div[@class='oxd-select-text-input']"
    PASSWORD_INPUT            = "(//input[@type='password'])[1]"
    CONFIRM_PASSWORD_INPUT    = "(//input[@type='password'])[2]"
    SAVE_BUTTON               = "//button[normalize-space()='Save']"
    CANCEL_BUTTON             = "//button[normalize-space()='Cancel']"

    # ── Personal Details (after save) ─────────────────────────────────────────
    # After saving Add Employee, OrangeHRM redirects to viewPersonalDetails.
    # The Employee ID is the second oxd-input--active on the page.
    PERSONAL_DETAILS_HEADER   = "//h6[text()='Personal Details']"
    EMPLOYEE_ID_DISPLAY       = "(//input[@class='oxd-input oxd-input--active'])[2]"

    # ── Validation / Error Messages ───────────────────────────────────────────
    REQUIRED_FIELD_ERROR      = "//span[text()='Required']"
    # When only one name field is missing, exactly one Required span appears.
    # Both FIRST_NAME_REQUIRED and LAST_NAME_REQUIRED point to the first span.
    FIRST_NAME_REQUIRED       = "(//span[text()='Required'])[1]"
    LAST_NAME_REQUIRED        = "(//span[text()='Required'])[1]"
    # Duplicate Employee ID error
    ALREADY_EXISTS_ERROR      = "//span[text()='Employee Id already exists']"
    PASSWORD_MISMATCH_ERROR   = "//span[text()='Passwords do not match']"
    INVALID_INPUT_ERROR       = "//span[contains(@class,'oxd-input-field-error-message')]"
    INVALID_ERROR             = "//span[contains(text(),'Invalid')]"

    # ── Employee List — Row Actions ───────────────────────────────────────────
    # Edit button: the pencil icon in each employee row
    EDIT_BUTTON_FIRST_ROW     = "//div[@class='oxd-table-body']//div[@role='row'][1]//button[1]"
    # Generic edit button by row index (1-based): use .format(n)
    EDIT_BUTTON_ROW           = "//div[@class='oxd-table-body']//div[@role='row'][{0}]//button[1]"

    # ── Employee List — Delete ────────────────────────────────────────────────
    # Checkbox in the first employee row (for selecting before delete)
    ROW_CHECKBOX_FIRST        = "//div[@class='oxd-table-body']//div[@role='row'][1]//div[@class='oxd-checkbox-wrapper']//input[@type='checkbox']"
    # Delete button in the first employee row (trash icon — second button)
    DELETE_BUTTON_FIRST_ROW   = "//div[@class='oxd-table-body']//div[@role='row']//button[2]"
    # Bulk delete button (top toolbar — appears after selecting rows)
    BULK_DELETE_BUTTON        = "//button[normalize-space()='Delete Selected']"
    # Confirmation modal — "Yes, Delete" button
    CONFIRM_DELETE_BUTTON     = "//button[normalize-space()='Yes, Delete']"
    # Confirmation modal — "No, Cancel" button
    CANCEL_DELETE_BUTTON      = "//button[normalize-space()='No, Cancel']"
    # Confirmation modal container
    DELETE_CONFIRM_MODAL      = "//div[contains(@class,'orangehrm-dialog-popup')]"

    # ── Personal Details — Edit Fields ────────────────────────────────────────
    # On the Personal Details page, First/Last Name inputs are read-only by default.
    # Clicking the pencil icon next to the name section enables editing.
    PERSONAL_DETAILS_EDIT_NAME_ICON = "//h6[text()='Personal Details']/following::button[contains(@class,'oxd-icon-button')][1]"
    PERSONAL_DETAILS_FIRST_NAME     = "//input[@name='firstName']"
    PERSONAL_DETAILS_LAST_NAME      = "//input[@name='lastName']"
    PERSONAL_DETAILS_SAVE_BUTTON    = "//button[normalize-space()='Save']"

    # ── Toast / Success Message ───────────────────────────────────────────────
    SUCCESS_TOAST             = "//div[contains(@class,'oxd-toast--success')]"
    TOAST_MESSAGE             = "//div[contains(@class,'oxd-toast-content-text')]"
