from pathlib import Path
from typing import Dict, Tuple

from tarsier._base import ITarsier
from tarsier._utils import load_js
from tarsier.adapter import AnyDriver, BrowserAdapter, adapter_factory
from tarsier.ocr import OCRService

TagToXPath = Dict[int, str]


class Tarsier(ITarsier):
    _JS_TAG_UTILS = Path(__file__).parent / "tag_utils.min.js"

    def __init__(self, ocr_service: OCRService):
        self._ocr_service = ocr_service
        self._js_utils = load_js(self._JS_TAG_UTILS)

    async def page_to_image(
        self, driver: AnyDriver, tag_text_elements: bool = False, tagless: bool = False
    ) -> Tuple[bytes, Dict[int, str]]:
        adapter = adapter_factory(driver)
        if not tagless:
            tag_to_xpath = await self._tag_page(adapter, tag_text_elements)
        screenshot = await self._take_screenshot(adapter)
        if not tagless:
            await self._remove_tags(adapter)
        return screenshot, tag_to_xpath if not tagless else {}

    async def page_to_text(
        self, driver: AnyDriver, tag_text_elements: bool = False, tagless: bool = False
    ) -> Tuple[str, TagToXPath]:
        image, tag_to_xpath = await self.page_to_image(
            driver, tag_text_elements, tagless
        )
        page_text = self._run_ocr(image)
        return page_text, tag_to_xpath

    @staticmethod
    async def _take_screenshot(adapter: BrowserAdapter) -> bytes:
        viewport = await adapter.get_viewport_size()
        default_width = viewport["width"]

        await adapter.set_viewport_size(default_width, viewport["content_height"])
        screenshot = await adapter.take_screenshot()
        await adapter.set_viewport_size(default_width, viewport["height"])

        return screenshot

    def _run_ocr(self, image: bytes) -> str:
        ocr_text = self._ocr_service.annotate(image)
        page_text = self._ocr_service.format_text(ocr_text)
        return page_text

    async def _tag_page(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> Dict[int, str]:
        await adapter.run_js(self._js_utils)

        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_xpath = await adapter.run_js(script)

        return {int(key): value for key, value in tag_to_xpath.items()}

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        script = "return window.removeTags();"

        await adapter.run_js(script)
