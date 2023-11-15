import asyncio
from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver

from tarsier.adapter._base import BrowserAdapter
from tarsier.adapter.types import ViewPortSize


class SeleniumAdapter(BrowserAdapter):
    def __init__(self, driver: WebDriver):
        self.driver = driver

    async def run_js(self, js: str) -> Any:
        return self.driver.execute_script(js)

    async def take_screenshot(self) -> bytes:
        return self.driver.get_screenshot_as_png()

    async def set_viewport_size(self, width: int, height: int) -> None:
        self.driver.set_window_size(width, height)

    async def get_viewport_size(self) -> ViewPortSize:
        script = "return [window.innerWidth, window.innerHeight, document.documentElement.scrollHeight];"
        width, height, content_height = self.driver.execute_script(script)
        return {"width": width, "height": height, "content_height": content_height}
