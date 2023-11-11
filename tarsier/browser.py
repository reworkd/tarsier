from abc import ABC, abstractmethod
from typing import Union, Dict, Tuple
import asyncio
import os
import json
from playwright.sync_api import Page as PageSync
from playwright.async_api import Page as PageAsync
from selenium.webdriver.remote.webdriver import WebDriver

from ocr import OCRService, GoogleVisionOCRService, ImageAnnotatorResponse


class BrowserDriver(ABC):
    @abstractmethod
    async def run_js(self, js: str):
        pass

    @abstractmethod
    async def take_screenshot(self, filename: str):
        pass

    @abstractmethod
    async def set_viewport_size(self, width: int, height: int):
        pass


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

    async def set_viewport_size(self, width, height):
        await asyncio.get_event_loop().run_in_executor(
            None, self.driver.set_window_size, width, height
        )


class PlaywrightSyncDriver(BrowserDriver):
    def __init__(self, page: PageSync):
        self.page = page

    async def run_js(self, js: str):
        return self.page.evaluate(js)

    async def take_screenshot(self, filename: str):
        self.page.screenshot(path=filename)

    async def set_viewport_size(self, width, height):
        self.page.set_viewport_size({"width": width, "height": height})


class PlaywrightAsyncDriver(BrowserDriver):
    def __init__(self, page: PageAsync):
        self.page = page

    async def run_js(self, js: str):
        result = await self.page.evaluate(js)
        return result

    async def take_screenshot(self, filename: str):
        await self.page.screenshot(path=filename)

    async def set_viewport_size(self, width, height):
        await self.page.set_viewport_size({"width": width, "height": height})


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

    def __init__(
        self, driver: Union[WebDriver, PageSync, PageAsync], ocr_service: OCRService
    ):
        self.driver = Tarsier.create_driver(driver)
        self.ocr_service = ocr_service
        self.loaded_tag_utils = False

    async def tag_page(self) -> Dict[int, str]:
        if not self.loaded_tag_utils:
            curr_dir = os.path.dirname(os.path.realpath(__file__))
            with open(f"{curr_dir}/tag_utils.js", "r") as f:
                await self.driver.run_js(f.read())

            self.loaded_tag_utils = True

        _, tag_to_xpath = await self.driver.run_js(f"tagifyWebpage(null, null);")
        return tag_to_xpath

    async def take_screenshot(self, filename: str) -> None:
        # TODO: scroll & stitch here, don't do viewport resizing
        default_width, default_height = await self.driver.run_js(
            "() => [window.innerWidth, window.innerHeight];"
        )
        content_height = await self.driver.run_js(
            "() => document.documentElement.scrollHeight;"
        )

        await self.driver.set_viewport_size(default_width, content_height)
        await self.driver.take_screenshot(filename)
        await self.driver.set_viewport_size(default_width, default_height)

    async def run_ocr(self, image: bytes) -> ImageAnnotatorResponse:
        return self.ocr_service.annotate(image)

    def format_ocr_to_text(self, ocr_text: ImageAnnotatorResponse) -> str:
        return self.ocr_service.format_text(ocr_text)

    async def page_to_text(self) -> Tuple[str, Dict[int, str]]:
        tag_to_xpath = await self.tag_page()
        await self.take_screenshot("screenshot.png") # TODO: probably not best naming practice?
        with open("screenshot.png", "rb") as f:
            image = f.read()
        ocr_text = await self.run_ocr(image)
        page_text = self.format_ocr_to_text(ocr_text)
        return page_text, tag_to_xpath


async def main():
    from playwright.async_api import async_playwright # TODO: test selenium and sync_playwright

    with open(
        "/Users/rohan/Documents/llama2d/llama2d/secrets/llama2d-dee298d9a98d.json", "r"
    ) as f:
        credentials = json.load(f)
    ocr_service = GoogleVisionOCRService(credentials)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://news.ycombinator.com/")

        tarsier = Tarsier(page, ocr_service)

        page_text, tag_to_xpath = await tarsier.page_to_text()
        print(page_text)
        print(tag_to_xpath)


if __name__ == "__main__":
    asyncio.run(main())
