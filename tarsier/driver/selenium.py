import asyncio

from selenium.webdriver.chrome.webdriver import WebDriver

from tarsier.driver._base import BrowserDriver


class SeleniumDriver(BrowserDriver):
    def __init__(self, driver: WebDriver):
        self.driver = driver

    async def run_js(self, js: str):
        return await asyncio.get_event_loop().run_in_executor(
            None, self.driver.execute_script, js
        )

    async def take_screenshot(self) -> bytes:
        raise NotImplementedError()
        # await asyncio.get_event_loop().run_in_executor(
        #     None, self.driver.save_screenshot, filename
        # )

    async def set_viewport_size(self, width, height):
        await asyncio.get_event_loop().run_in_executor(
            None, self.driver.set_window_size, width, height
        )
