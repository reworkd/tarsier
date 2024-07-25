from asyncio import Protocol
from pathlib import Path
from typing import Dict, Tuple, Any, TypedDict
from PIL import Image
from io import BytesIO
import html2text
import json

from tarsier._utils import load_js
from tarsier.adapter import AnyDriver, BrowserAdapter, adapter_factory
from tarsier.ocr import OCRService, ImageAnnotatorResponse
from tarsier.ocr.types import ImageAnnotation
from tarsier.text_format import format_text

TagToXPath = Dict[int, str]


class ColouredElem(TypedDict):
    id: int
    idSymbol: str
    color: str
    xpath: str
    midpoint: Tuple[float, float]
    normalizedMidpoint: Tuple[float, float]
    width: float
    height: float
    isFixed: bool
    fixedPosition: str


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
    ) -> Tuple[bytes, Dict[int, str]]:
        adapter = adapter_factory(driver)
        tag_to_xpath = (
            await self._tag_page(adapter, tag_text_elements) if not tagless else {}
        )
        screenshot = await self._take_screenshot(adapter)
        if not tagless:
            await self._remove_tags(adapter)
        return screenshot, tag_to_xpath if not tagless else {}

    async def page_to_text(
        self, driver: AnyDriver, tag_text_elements: bool = False, tagless: bool = False
    ) -> Tuple[str, TagToXPath]:
        adapter = adapter_factory(driver)
        untagged_image = await self._take_screenshot(adapter)
        untagged_ocr_annotations = self._ocr_service.annotate(untagged_image)

        if tagless:
            text = format_text(untagged_ocr_annotations)
            return text, {}

        # tag_to_xpath = await self._tag_page(adapter, tag_text_elements)
        # await self._hide_non_tag_elements(adapter)
        # tagged_image = await self._take_screenshot(adapter)
        # await self._revert_visibilities(adapter)
        # await self._remove_tags(adapter)
        # tagged_ocr_annotations = self._ocr_service.annotate(tagged_image)

        colour_mapping = await self._colour_based_tagify(adapter, tag_text_elements)
        tag_to_xpath = {item['id']: item['xpath'] for item in colour_mapping}
        await self._hide_non_coloured_elements(adapter)
        coloured_image = await self._take_screenshot(adapter)
        unique_colours = await self._check_colours(coloured_image)
        # remove the colours from colour_mapping that are not common between unique_colours and colour_mapping
        common_colour_mapping = [item for item in colour_mapping if item['color'] in unique_colours]

        coloured_annotations: ImageAnnotatorResponse = [
            ImageAnnotation(
                text=item['idSymbol'],
                midpoint=item['midpoint'],
                midpoint_normalized=item['normalizedMidpoint'],
                width=item['width'],
                height=item['height']
            )
            for item in common_colour_mapping
        ]

        combined_annotations = self.combine_annotations(
            untagged_ocr_annotations, coloured_annotations
        )
        combined_text = format_text(combined_annotations)

        return combined_text, tag_to_xpath

    async def page_to_text_new(
        self, driver: AnyDriver, tag_text_elements: bool = False
    ) -> Tuple[str, TagToXPath]:

        adapter = adapter_factory(driver)
        colour_mapping = await self._colour_based_tagify(adapter, tag_text_elements)
        tag_to_xpath = {item['id']: item['xpath'] for item in colour_mapping}
        await self._hide_non_coloured_elements(adapter)
        coloured_image = await self._take_screenshot(adapter)
        unique_colours = await self._check_colours(coloured_image)
        # remove the colours from colour_mapping that are not common between unique_colours and colour_mapping
        common_colour_mapping = [item for item in colour_mapping if item['color'] in unique_colours]

        # create the bounding boxes
        await self._create_text_bounding_boxes(adapter)
        document_dimensions_script = "return window.documentDimensions();"
        document_dimensions = await adapter.run_js(document_dimensions_script)
        document_width = document_dimensions['width']
        document_height = document_dimensions['height']

        annotations: ImageAnnotatorResponse = []
        fixed_top_annotations: ImageAnnotatorResponse = []
        fixed_bottom_annotations: ImageAnnotatorResponse = []

        for item in common_colour_mapping:
            xpath = item['xpath']

            # Check if the element has child elements that are tagged
            has_tagged_children = await self._check_has_tagged_children(adapter, xpath)

            if has_tagged_children:
                # Only create an annotation for the tag itself
                midpoint = item['midpoint']
                normalized_midpoint = item['normalizedMidpoint']
                tag_annotation = ImageAnnotation(
                    text=item['idSymbol'],
                    midpoint=midpoint,
                    midpoint_normalized=normalized_midpoint,
                    width=int(item['width']),
                    height=int(item['height'])
                )
                if item['isFixed'] and item['fixedPosition'] == 'top':
                    fixed_top_annotations.append(tag_annotation)
                elif item['isFixed'] and item['fixedPosition'] == 'bottom':
                    fixed_bottom_annotations.append(tag_annotation)
                else:
                    annotations.append(tag_annotation)
            else:
                # Create annotations for each bounding box
                bounding_boxes_script = f"return window.getElementBoundingBoxes({json.dumps(xpath)});"
                bounding_boxes = await adapter.run_js(bounding_boxes_script)

                for i, box in enumerate(bounding_boxes):
                    text = box['text']
                    midpoint = (box['left'], box['top'] + box['height'])
                    normalized_midpoint = (
                        midpoint[0] / document_width,
                        midpoint[1] / document_height
                    )
                    width = box['width']
                    height = box['height']

                    if i == 0:
                        text = item['idSymbol'] + " " + text
                        width = width + 48

                    annotation = ImageAnnotation(
                        text=text,
                        midpoint=midpoint,
                        midpoint_normalized=normalized_midpoint,
                        width=width,
                        height=height
                    )
                    if item['isFixed']:
                        if item['fixedPosition'] == 'top':
                            fixed_top_annotations.append(annotation)
                        elif item['fixedPosition'] == 'bottom':
                            fixed_bottom_annotations.append(annotation)
                    else:
                        annotations.append(annotation)


        # sort annotations before combining
        fixed_top_annotations = self.sort_annotations(fixed_top_annotations)
        annotations = self.sort_annotations(annotations)
        fixed_bottom_annotations = self.sort_annotations(fixed_bottom_annotations)
        # Combine the annotations in the correct order
        combined_annotations = fixed_top_annotations + annotations + fixed_bottom_annotations

        annotations_formatted = format_text(combined_annotations)
        return annotations_formatted, tag_to_xpath

    @staticmethod
    def sort_annotations(annotations: ImageAnnotatorResponse) -> ImageAnnotatorResponse:
        return sorted(annotations, key=lambda x: (x['midpoint_normalized'][1], x['midpoint_normalized'][0]))


    @staticmethod
    def combine_annotations(
        untagged_annotation: ImageAnnotatorResponse,
        tagged_annotation: ImageAnnotatorResponse,
    ) -> ImageAnnotatorResponse:
        combined_annotations: ImageAnnotatorResponse = untagged_annotation + tagged_annotation
        combined_annotations = list(
            sorted(
                combined_annotations,
                key=lambda x: (
                    x["midpoint_normalized"][1],
                    x["midpoint_normalized"][0],
                ),
            )
        )
        return combined_annotations

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
        print("Ran JS")
        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_xpath = await adapter.run_js(script)

        return {int(key): value for key, value in tag_to_xpath.items()}

    @staticmethod
    async def get_element_text(adapter: BrowserAdapter, xpath: str) -> str:
        safe_xpath = json.dumps(xpath)
        script = f"return window.getElementHtmlByXPath({safe_xpath});"
        print(f"Executing script: {script}")
        try:
            html_content = await adapter.run_js(script)
        except Exception as e:
            print(f"Error executing script: {e}")
            raise
        raw_text = html2text.html2text(html_content)

        return raw_text

    async def _colour_based_tagify(
            self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> list[ColouredElem]:
        await adapter.run_js(self._js_utils)

        script = f"return window.colourBasedTagify({str(tag_text_elements).lower()});"
        colour_mapping = await adapter.run_js(script)
        return colour_mapping

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        await adapter.run_js(self._js_utils)
        script = "return window.removeTags();"

        await adapter.run_js(script)

    @staticmethod
    async def _check_has_tagged_children(adapter: BrowserAdapter, xpath: str) -> bool:
        script = f"return window.checkHasTaggedChildren({json.dumps(xpath)});"

        return await adapter.run_js(script)

    @staticmethod
    async def _hide_non_tag_elements(adapter: BrowserAdapter) -> None:
        script = "return window.hideNonTagElements();"

        await adapter.run_js(script)

    @staticmethod
    async def _revert_visibilities(adapter: BrowserAdapter) -> None:
        script = "return window.revertVisibilities();"

        await adapter.run_js(script)

    @staticmethod
    async def _check_colours(image: bytes) -> list[str]:
        image = Image.open(BytesIO(image))
        image = image.convert('RGB')

        width, height = image.size
        unique_colors = set()

        # looping through each pixel
        for x in range(width):
            for y in range(height):
                color = image.getpixel((x, y))
                unique_colors.add(color)

        unique_colors_list = [f'rgb({r}, {g}, {b})' for r, g, b in unique_colors]

        return unique_colors_list

    @staticmethod
    async def _hide_non_coloured_elements(adapter: BrowserAdapter) -> None:
        script = "return window.hideNonColouredElements();"
        await adapter.run_js(script)

    @staticmethod
    async def _create_text_bounding_boxes(adapter: BrowserAdapter) -> None:
        script = "return window.createTextBoundingBoxes();"
        await adapter.run_js(script)
