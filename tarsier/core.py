from asyncio import Protocol
from pathlib import Path
from typing import Tuple, Optional, TypedDict

from tarsier._utils import load_js
from tarsier.adapter import AnyDriver, BrowserAdapter, adapter_factory
from tarsier.ocr import OCRService
from tarsier.text_format import format_text


class TagMetadata(TypedDict):
    tarsier_id: int
    element_name: str
    opening_tag_html: str
    xpath: str
    element_text: Optional[str]
    text_node_index: Optional[int]
    id_symbol: str
    id_string: str


class ITarsier(Protocol):
    async def page_to_image(
        self, driver: AnyDriver
    ) -> Tuple[bytes, dict[int, TagMetadata]]:
        raise NotImplementedError()

    async def page_to_text(
        self, driver: AnyDriver
    ) -> Tuple[str, dict[int, TagMetadata]]:
        raise NotImplementedError()

    async def page_to_image_and_text(
        self, driver: AnyDriver
    ) -> Tuple[bytes, str, dict[int, TagMetadata]]:
        raise NotImplementedError()


class Tarsier(ITarsier):
    _JS_TAG_UTILS = Path(__file__).parent / "tag_utils.min.js"

    def __init__(self, ocr_service: OCRService):
        self._ocr_service = ocr_service
        self._js_utils = load_js(self._JS_TAG_UTILS)

    async def page_to_image(
        self,
        driver: AnyDriver,
        tag_text_elements: bool = False,
        tagless: bool = False,
        keep_tags_showing: bool = False,
    ) -> Tuple[bytes, dict[int, TagMetadata]]:
        adapter = adapter_factory(driver)
        tag_to_xpath = (
            await self._tag_page(adapter, tag_text_elements) if not tagless else {}
        )
        if tagless:
            await self._remove_tags(adapter)

        screenshot = await self._take_screenshot(adapter)

        if not keep_tags_showing:
            await self._remove_tags(adapter)

        return screenshot, tag_to_xpath if not tagless else {}

    async def page_to_text(
        self,
        driver: AnyDriver,
        tag_text_elements: bool = False,
        tagless: bool = False,
        keep_tags_showing: bool = False,
    ) -> Tuple[str, dict[int, TagMetadata]]:
        image, tag_to_xpath = await self.page_to_image(
            driver, tag_text_elements, tagless, keep_tags_showing
        )
        page_text = self._run_ocr(image)
        return page_text, tag_to_xpath

    async def page_to_image_and_text(
        self,
        driver: AnyDriver,
        tag_text_elements: bool = False,
        tagless: bool = False,
        keep_tags_showing: bool = False,
    ) -> Tuple[bytes, str, dict[int, TagMetadata]]:
        image, tag_to_xpath = await self.page_to_image(
            driver, tag_text_elements, tagless, keep_tags_showing
        )
        page_text = self._run_ocr(image)
        return image, page_text, tag_to_xpath

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
        page_text = format_text(ocr_text)
        return page_text

    async def _tag_page(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> dict[int, TagMetadata]:
        await self._load_tarsier_utils(adapter)

        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_meta = await adapter.run_js(script)

        tag_metadata_dict = {}
        for tarsier_id_str, meta in tag_to_meta.items():
            tarsier_id = int(tarsier_id_str)
            tag_metadata_dict[tarsier_id] = TagMetadata(
                tarsier_id=meta["tarsierId"],
                element_name=meta["elementName"],
                opening_tag_html=meta["openingTagHTML"],
                xpath=meta["xpath"],
                element_text=meta.get("elementText"),
                text_node_index=meta.get("textNodeIndex"),
                id_symbol=meta["idSymbol"],
                id_string=meta["idString"],
            )
        return tag_metadata_dict

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        await self._load_tarsier_utils(adapter)
        script = "return window.removeTags();"

        await adapter.run_js(script)

    async def remove_tags(self, driver: AnyDriver) -> None:
        adapter = adapter_factory(driver)
        await self._remove_tags(adapter)

    async def _load_tarsier_utils(self, adapter: BrowserAdapter) -> None:
        await adapter.run_js(self._js_utils)
