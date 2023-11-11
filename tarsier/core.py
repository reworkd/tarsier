import os
from typing import Dict, Tuple

from tarsier._base import ITarsier
from tarsier.driver import BrowserDriver, SeleniumDriver
from tarsier.ocr import OCRService

TagToXPath = Dict[int, str]


class Tarsier(ITarsier):
    _JS_TAG_UTILS = os.path.dirname(os.path.realpath(__file__)) + "/tag_utils.js"

    def __init__(self, ocr_service: OCRService):
        self._ocr_service = ocr_service
        with open(self._JS_TAG_UTILS, "r") as f:
            self._js_utils = f.read()

    async def page_to_image(
        self, driver: BrowserDriver
    ) -> Tuple[bytes, Dict[int, str]]:
        tag_to_xpath = await self._tag_page(driver)

        screenshot = await self._take_screenshot(driver)
        return screenshot, tag_to_xpath

    async def page_to_text(self, driver: BrowserDriver) -> Tuple[str, TagToXPath]:
        image, tag_to_xpath = await self.page_to_image(driver)
        page_text = self._run_ocr(image)
        return page_text, tag_to_xpath

    @staticmethod
    async def _take_screenshot(driver: BrowserDriver) -> bytes:
        # TODO: scroll & stitch here, don't do viewport resizing
        script = "() => [window.innerWidth, window.innerHeight, document.documentElement.scrollHeight];"
        if isinstance(driver, SeleniumDriver):
            script = f"return [window.innerWidth, window.innerHeight, document.documentElement.scrollHeight];"

        default_width, default_height, content_height = await driver.run_js(script)

        await driver.set_viewport_size(default_width, content_height)
        screenshot = await driver.take_screenshot()
        await driver.set_viewport_size(default_width, default_height)

        return screenshot

    def _run_ocr(self, image: bytes) -> str:
        ocr_text = self._ocr_service.annotate(image)
        page_text = self._ocr_service.format_text(ocr_text)
        return page_text

    async def _tag_page(self, driver: BrowserDriver) -> Dict[int, str]:
        await driver.run_js(self._js_utils)

        script = "tagifyWebpage(null, null);"
        if isinstance(driver, SeleniumDriver):
            script = f"return window.{script}"

        _, tag_to_xpath = await driver.run_js(script)
        return {int(key): value for key, value in tag_to_xpath.items()}
