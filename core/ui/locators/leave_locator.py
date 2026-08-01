"""
Leave Module Locators
=====================
Element selectors for the Leave > Apply and My Leave pages.
All locators are class-based string constants — no inline strings in tests.
"""


class LeaveApplyLocator:
    """Locators for the Leave > Apply page."""

    # Navigation
    LEAVE_MENU    = "//span[normalize-space()='Leave']"
    APPLY_SUBMENU = "//a[normalize-space()='Apply']"

    # Form fields
    LEAVE_TYPE_DROPDOWN = ".oxd-select-text-input"
    LEAVE_TYPE_OPTION   = "//div[@role='listbox']//span[normalize-space()='{0}']"
    FROM_DATE_INPUT     = "//label[text()='From Date']/../following-sibling::div//input"
    TO_DATE_INPUT       = "//label[text()='To Date']/../following-sibling::div//input"
    COMMENTS_TEXTAREA   = "//label[text()='Comments']/../following-sibling::div//textarea"

    # Actions
    APPLY_BUTTON = "//button[@type='submit' and normalize-space()='Apply']"

    # Feedback
    SUCCESS_MESSAGE  = "//div[contains(@class,'oxd-toast--success')]"
    ERROR_MESSAGE    = "//div[contains(@class,'oxd-toast--error')]"
    VALIDATION_ERROR = "//span[contains(@class,'oxd-input-field-error-message')]"
    BALANCE_DISPLAY  = "//p[contains(@class,'orangehrm-leave-balance-text')]"


class MyLeaveLocator:
    """Locators for the My Leave list page."""

    MY_LEAVE_MENU    = "//a[normalize-space()='My Leave']"
    LEAVE_LIST_TABLE = "//div[contains(@class,'orangehrm-leave-list')]"
    LEAVE_ROW        = "//div[contains(@class,'oxd-table-card')]"

    # Table cell positions (1-based column index)
    LEAVE_TYPE_CELL = "//div[contains(@class,'oxd-table-cell')][4]"
    FROM_DATE_CELL  = "//div[contains(@class,'oxd-table-cell')][5]"
    TO_DATE_CELL    = "//div[contains(@class,'oxd-table-cell')][6]"
    STATUS_CELL     = "//div[contains(@class,'oxd-table-cell')][7]"
