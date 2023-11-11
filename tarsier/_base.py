from asyncio import Protocol
from typing import Dict, Tuple, Union

from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync
from selenium.webdriver.remote.webdriver import WebDriver

from tarsier.driver import BrowserDriver, driver_factory

Driver = Union[WebDriver, PageSync, PageAsync]


class ITarsier(Protocol):
    async def page_to_image(self, driver: BrowserDriver) -> Tuple[str, Dict[int, str]]:
        ...

    async def page_to_text(self, driver: BrowserDriver) -> Tuple[str, Dict[int, str]]:
        ...

    @staticmethod
    def create_driver(driver: Driver) -> BrowserDriver:
        return driver_factory(driver)
