from typing import Union

from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync
from selenium.webdriver.chrome.webdriver import WebDriver

from ._base import BrowserDriver
from .playwright import PlaywrightAsyncDriver, PlaywrightSyncDriver
from .selenium import SeleniumDriver

# TODO: make selenium and playwright drivers options[


def driver_factory(driver: Union[WebDriver, PageSync, PageAsync]):
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
]
