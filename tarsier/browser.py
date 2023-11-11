from abc import ABC, abstractmethod
import os
from typing import Union, Dict
import asyncio
from playwright.sync_api import Page as PageSync
from playwright.async_api import Page as PageAsync
from selenium.webdriver.remote.webdriver import WebDriver


class BrowserDriver(ABC):
    @abstractmethod
    async def run_js(self, js: str):
        pass

    @abstractmethod
    async def take_screenshot(self, filename: str):
        pass

    async def set_viewport_size(self, width, height):
        await self.run_js(
            f"""
            document.documentElement.style.width = '{width}px';
            document.documentElement.style.height = '{height}px';
            """
        )


class SeleniumDriver(BrowserDriver):
    def __init__(self, driver: WebDriver):
        self.driver = driver

    async def run_js(self, js: str):
        return await asyncio.get_event_loop().run_in_executor(
            None, self.driver.execute_script, js
        )

    async def take_screenshot(self, filename: str):
        await asyncio.get_event_loop().run_in_executor(
            None, self.driver.save_screenshot, filename
        )


class PlaywrightSyncDriver(BrowserDriver):
    def __init__(self, page: PageSync):
        self.page = page

    async def run_js(self, js: str):
        return await self.page.evaluate(js)

    async def take_screenshot(self, filename: str):
        await self.page.screenshot(path=filename)


class PlaywrightAsyncDriver(BrowserDriver):
    def __init__(self, page: PageAsync):
        self.page = page

    async def run_js(self, js: str):
        return await self.page.evaluate(js)

    async def take_screenshot(self, filename: str):
        await self.page.screenshot(path=filename)


class Tarsier:
    @staticmethod
    def create_driver(driver: Union[WebDriver, PageSync, PageAsync]):
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

    def __init__(self, driver: Union[WebDriver, PageSync, PageAsync]):
        self.driver = Tarsier.create_driver(driver)
        
        self.loaded_tag_utils = False

    async def tag_page(self) -> Dict[int, str]:
        if not self.loaded_tag_utils:
            curr_dir = os.path.dirname(os.path.realpath(__file__))
            with open(f"{curr_dir}/tag_utils.js", "r") as f:
                await self.driver.run_js(f.read())
            
            self.loaded_tag_utils = True

        _, tag_to_xpath =  await self.driver.run_js(f"tagifyWebpage(null, null)")
        return tag_to_xpath

    async def take_screenshot(self, filename: str) -> None:
        # TODO: scroll & stitch here, don't do viewport resizing
        default_width, default_height = await self.driver.run_js(
            "return [window.innerWidth, window.innerHeight]"
        )
        content_height = await self.driver.run_js(
            "return document.documentElement.scrollHeight"
        )

        await self.driver.set_viewport_size(default_width, content_height)
        await self.driver.take_screenshot(filename)
        await self.driver.set_viewport_size(default_width, default_height)


if __name__ == "__main__":
    pass
