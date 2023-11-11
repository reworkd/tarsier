from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync
from selenium.webdriver.remote.webdriver import WebDriver

from ._base import BrowserAdapter
from .playwright import PlaywrightAsyncAdapter, PlaywrightSyncAdapter
from .selenium import SeleniumAdapter
from .types import AnyDriver

# TODO: make selenium and playwright drivers optional


def adapter_factory(driver: AnyDriver) -> BrowserAdapter:
    if isinstance(driver, WebDriver):
        return SeleniumAdapter(driver)
    elif isinstance(driver, PageSync):
        return PlaywrightSyncAdapter(driver)
    elif isinstance(driver, PageAsync):
        return PlaywrightAsyncAdapter(driver)
    # TODO: add support for Puppeteer

    else:
        raise ValueError(
            "Invalid driver type: please provide a Selenium WebDriver or a Playwright Page"
        )


__all__ = [
    "BrowserAdapter",
    "PlaywrightAsyncAdapter",
    "PlaywrightSyncAdapter",
    "SeleniumAdapter",
    "adapter_factory",
    "AnyDriver",
]
