from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync
from selenium.webdriver.remote.webdriver import WebDriver

from ._base import BrowserDriver
from .playwright import PlaywrightAsyncDriver, PlaywrightSyncDriver
from .selenium import SeleniumDriver
from .types import AnyDriver

# TODO: make selenium and playwright drivers optional


def driver_factory(driver: AnyDriver) -> BrowserDriver:
    if isinstance(driver, WebDriver):
        return SeleniumDriver(driver)
    elif isinstance(driver, PageSync):
        return PlaywrightSyncDriver(driver)
    elif isinstance(driver, PageAsync):
        return PlaywrightAsyncDriver(driver)
    # TODO: add support for Puppeteer

    else:
        raise ValueError(
            "Invalid driver type: please provide a Selenium WebDriver or a Playwright Page"
        )


__all__ = [
    "BrowserDriver",
    "PlaywrightAsyncDriver",
    "PlaywrightSyncDriver",
    "SeleniumDriver",
    "driver_factory",
    "AnyDriver",
]
