from playwright.sync_api import Page


class LeftMenuLocator:
    """
    Left navigation menu locators — URL-based to be language-agnostic.
    OrangeHRM may display the UI in different languages depending on the
    user's locale setting. Using href-based locators ensures reliability
    regardless of the display language.
    """

    def __init__(self, page: Page):
        self.admin       = page.locator("//a[@href='/web/index.php/admin/viewAdminModule']")
        self.pim         = page.locator("//a[@href='/web/index.php/pim/viewPimModule']")
        self.leave       = page.locator("//a[@href='/web/index.php/leave/viewLeaveModule']")
        self.time        = page.locator("//a[@href='/web/index.php/time/viewTimeModule']")
        self.recruitment = page.locator("//a[@href='/web/index.php/recruitment/viewRecruitmentModule']")
        self.my_info     = page.locator("//a[@href='/web/index.php/pim/viewMyDetails']")
        self.performance = page.locator("//a[@href='/web/index.php/performance/viewPerformanceModule']")
        self.dashboard   = page.locator("//a[@href='/web/index.php/dashboard/index']")
        self.directory   = page.locator("//a[@href='/web/index.php/directory/viewDirectory']")
        self.maintenance = page.locator("//a[@href='/web/index.php/maintenance/viewMaintenanceModule']")
        self.claim       = page.locator("//a[@href='/web/index.php/claim/viewClaimModule']")
        self.buzz        = page.locator("//a[@href='/web/index.php/buzz/viewBuzz']")
