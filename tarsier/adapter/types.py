from typing import TypedDict, Union

from playwright.async_api import Page as PageAsync
from playwright.sync_api import Page as PageSync
from selenium.webdriver.remote.webdriver import WebDriver

AnyDriver = Union[WebDriver, PageSync, PageAsync]


class ViewPortSize(TypedDict):
    width: int
    height: int
    content_height: int
