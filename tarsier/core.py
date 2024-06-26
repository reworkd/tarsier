from asyncio import Protocol
from pathlib import Path
from typing import Dict, Tuple

from tarsier._utils import load_js
from tarsier.adapter import AnyDriver, BrowserAdapter, adapter_factory
from tarsier.ocr import OCRService
from tarsier.text_format import format_text

TagToXPath = Dict[int, str]


class ITarsier(Protocol):
    async def page_to_image(self, driver: AnyDriver) -> Tuple[bytes, Dict[int, str]]:
        raise NotImplementedError()

    async def page_to_text(self, driver: AnyDriver) -> Tuple[str, Dict[int, str]]:
        raise NotImplementedError()


class Tarsier(ITarsier):
    _JS_TAG_UTILS = Path(__file__).parent / "tag_utils.min.js"

    def __init__(self, ocr_service: OCRService):
        self._ocr_service = ocr_service
        self._js_utils = load_js(self._JS_TAG_UTILS)

    async def page_to_image(
        self, driver: AnyDriver, tag_text_elements: bool = False, tagless: bool = False
    ) -> Tuple[bytes, bytes, Dict[int, str]]:
        adapter = adapter_factory(driver)
        initial_screenshot = await self._take_screenshot(adapter)
        tag_to_xpath = (
            await self._tag_page(adapter, tag_text_elements) if not tagless else {}
        )
        await self._hide_non_tag_elem(adapter)
        tagged_screenshot = await self._take_screenshot(adapter)
        await self._revert_visibilities(adapter)
        if not tagless:
            await self._remove_tags(adapter)
        return initial_screenshot, tagged_screenshot, tag_to_xpath if not tagless else {}

    async def page_to_text(
        self, driver: AnyDriver, tag_text_elements: bool = False, tagless: bool = False
    ) -> Tuple[ str, TagToXPath]:
        untagged_image, tagged_image, tag_to_xpath = await self.page_to_image(
            driver, tag_text_elements, tagless
        )
        untagged_ocr_annotations = self._ocr_service.annotate(untagged_image)
        tagged_ocr_annotations = self._ocr_service.annotate(tagged_image)

        combined_annotations = {'words': untagged_ocr_annotations["words"] + tagged_ocr_annotations["words"]}
        combined_annotations['words'] = list(
            sorted(
                combined_annotations['words'],
                key=lambda x: (
                    x["midpoint_normalized"][1],
                    x["midpoint_normalized"][0],
                ),
            )
        )

        combined_text = format_text(combined_annotations)

        return combined_text, tag_to_xpath

    @staticmethod
    async def _take_screenshot(adapter: BrowserAdapter) -> bytes:
        viewport = await adapter.get_viewport_size()
        default_width = viewport["width"]

        await adapter.set_viewport_size(default_width, viewport["content_height"])
        screenshot = await adapter.take_screenshot()
        await adapter.set_viewport_size(default_width, viewport["height"])

        return screenshot

    async def _tag_page(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> Dict[int, str]:
        await adapter.run_js(self._js_utils)

        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_xpath = await adapter.run_js(script)

        return {int(key): value for key, value in tag_to_xpath.items()}

    @staticmethod
    async def _remove_tags(adapter: BrowserAdapter) -> None:
        script = "return window.removeTags();"

        await adapter.run_js(script)

    @staticmethod
    async def _hide_non_tag_elem(adapter: BrowserAdapter) -> None:
        script = "return window.hideNonTagElements();"

        await adapter.run_js(script)

    @staticmethod
    async def _revert_visibilities(adapter: BrowserAdapter) -> None:
        script = "return window.revertVisibilities();"

        await adapter.run_js(script)