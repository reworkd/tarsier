from asyncio import Protocol
from pathlib import Path
from typing import Dict, Tuple, Optional

from tarsier._utils import load_js
from tarsier.adapter import AnyDriver, BrowserAdapter, adapter_factory
from tarsier.ocr import OCRService
from tarsier.text_format import format_text

TagToXPath = Dict[int, str]


class TagMetadata:
    def __init__(
        self,
        tarsierID: int,
        elementName: str,
        elementHTML: str,
        xpath: str,
        elementText: Optional[str],
        textNodeIndex: Optional[int],
        idSymbol: str,
        idString: str,
    ):
        self.tarsierID = tarsierID
        self.elementName = elementName
        self.elementHTML = elementHTML
        self.xpath = xpath
        self.elementText = elementText
        self.textNodeIndex = textNodeIndex
        self.idSymbol = idSymbol
        self.idString = idString

    def __repr__(self):
        return f"TagMetadata(tarsierID={self.tarsierID}, elementName={self.elementName}, xpath={self.xpath})"


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
        self,
        driver: AnyDriver,
        tag_text_elements: bool = False,
        tagless: bool = False,
        keep_tags_showing: bool = False,
    ) -> Tuple[bytes, list[TagMetadata]]:
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
    ) -> Tuple[str, list[TagMetadata]]:
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
    ) -> Tuple[bytes, str, list[TagMetadata]]:
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
    ) -> list[TagMetadata]:
        await self._load_tarsier_utils(adapter)

        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_meta = await adapter.run_js(script)

        tag_metadata_list = [
            TagMetadata(
                tarsierID=meta["tarsierID"],
                elementName=meta["elementName"],
                elementHTML=meta["elementHTML"],
                xpath=meta["xpath"],
                elementText=meta.get("elementText"),
                textNodeIndex=meta.get("textNodeIndex"),
                idSymbol=meta["idSymbol"],
                idString=meta["idString"],
            )
            for meta in tag_to_meta
        ]
        return tag_metadata_list

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        await self._load_tarsier_utils(adapter)
        script = "return window.removeTags();"

        await adapter.run_js(script)

    async def remove_tags(self, driver: AnyDriver) -> None:
        adapter = adapter_factory(driver)
        await self._remove_tags(adapter)

    async def _load_tarsier_utils(self, adapter: BrowserAdapter) -> None:
        await adapter.run_js(self._js_utils)
