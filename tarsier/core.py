import os
from typing import Dict, Tuple

from tarsier._base import ITarsier
from tarsier.adapter import AnyDriver, BrowserAdapter, SeleniumAdapter, adapter_factory
from tarsier.ocr import OCRService

TagToXPath = Dict[int, str]


class Tarsier(ITarsier):
    _JS_TAG_UTILS = os.path.dirname(os.path.realpath(__file__)) + "/tag_utils.js"

    def __init__(self, ocr_service: OCRService):
        self._ocr_service = ocr_service
        with open(self._JS_TAG_UTILS, "r") as f:
            self._js_utils = f.read()

    async def page_to_image(self, driver: AnyDriver, tag_text_elements: bool = False) -> Tuple[bytes, Dict[int, str]]:
        adapter = adapter_factory(driver)
        tag_to_xpath = await self._tag_page(adapter, tag_text_elements)
        screenshot = await self._take_screenshot(adapter)
        await self._remove_tags(adapter)
        return screenshot, tag_to_xpath

    async def page_to_text(self, driver: AnyDriver, tag_text_elements: bool = False) -> Tuple[str, TagToXPath]:
        image, tag_to_xpath = await self.page_to_image(driver, tag_text_elements)
        page_text = self._run_ocr(image)
        return page_text, tag_to_xpath

    @staticmethod
    async def _take_screenshot(adapter: BrowserAdapter) -> bytes:
        # TODO: scroll & stitch here, don't do viewport resizing
        script = "() => [window.innerWidth, window.innerHeight, document.documentElement.scrollHeight];"
        if isinstance(adapter, SeleniumAdapter):
            script = f"return [window.innerWidth, window.innerHeight, document.documentElement.scrollHeight];"

        default_width, default_height, content_height = await adapter.run_js(script)

        await adapter.set_viewport_size(default_width, content_height)
        screenshot = await adapter.take_screenshot()
        await adapter.set_viewport_size(default_width, default_height)

        return screenshot

    def _run_ocr(self, image: bytes) -> str:
        ocr_text = self._ocr_service.annotate(image)
        page_text = self._ocr_service.format_text(ocr_text)
        return page_text

    async def _tag_page(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> Dict[int, str]:
        await adapter.run_js(self._js_utils)

        script = f"tagifyWebpage({str(tag_text_elements).lower()});"
        if isinstance(adapter, SeleniumAdapter):
            script = f"return window.{script}"

        tag_to_xpath = await adapter.run_js(script)
        return {int(key): value for key, value in tag_to_xpath.items()}

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        # await adapter.run_js(self._js_utils)

        script = "removeTags();"
        if isinstance(adapter, SeleniumAdapter):
            script = f"return window.{script}"

        await adapter.run_js(script)
        return None
