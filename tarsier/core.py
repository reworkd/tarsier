import os
from typing import Dict, Tuple

from tarsier._base import ITarsier
from tarsier.driver import BrowserDriver
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

        await self._take_screenshot(
            driver, "screenshot.png"
        )  # TODO: probably not best naming practice?

        with open("screenshot.png", "rb") as f:
            return f.read(), tag_to_xpath

    async def page_to_text(self, driver: BrowserDriver) -> Tuple[str, TagToXPath]:
        image, tag_to_xpath = await self.page_to_image(driver)
        page_text = await self._run_ocr(image)
        return page_text, tag_to_xpath

    @staticmethod
    async def _take_screenshot(driver: BrowserDriver, filename: str) -> None:
        # TODO: scroll & stitch here, don't do viewport resizing
        default_width, default_height = await driver.run_js(
            "() => [window.innerWidth, window.innerHeight];"
        )
        content_height = await driver.run_js(
            "() => document.documentElement.scrollHeight;"
        )

        await driver.set_viewport_size(default_width, content_height)
        await driver.take_screenshot(filename)
        await driver.set_viewport_size(default_width, default_height)

    async def _run_ocr(self, image: bytes) -> str:
        ocr_text = self._ocr_service.annotate(image)
        page_text = self._ocr_service.format_text(ocr_text)
        return page_text

    async def _tag_page(self, driver: BrowserDriver) -> Dict[int, str]:
        await driver.run_js(self._js_utils)
        _, tag_to_xpath = await driver.run_js(f"tagifyWebpage(null, null);")
        return tag_to_xpath
