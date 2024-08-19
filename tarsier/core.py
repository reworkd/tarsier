from asyncio import Protocol
from pathlib import Path
from typing import Dict, Tuple, TypedDict
from PIL import Image
from io import BytesIO
import json

import numpy as np
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
    boundingBoxX: float
    boundingBoxY: float


class BoundingBox(TypedDict):
    left: int
    top: int
    width: int
    height: int


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
    ) -> Tuple[bytes, TagToXPath]:
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
    ) -> Tuple[str, TagToXPath]:
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
    ) -> Tuple[bytes, str, TagToXPath]:
        image, tag_to_xpath = await self.page_to_image(
            driver, tag_text_elements, tagless, keep_tags_showing
        )
        page_text = self._run_ocr(image)
        return image, page_text, tag_to_xpath

    async def page_to_text_colour_tag(
        self, driver: AnyDriver, tag_text_elements: bool = False
    ) -> Tuple[str, TagToXPath]:
        adapter = adapter_factory(driver)

        coloured_elems, inserted_id_strings = await self._colour_based_tagify(
            adapter, tag_text_elements
        )

        tag_to_xpath = {elem["id"]: elem["xpath"] for elem in coloured_elems}
        await self._hide_non_coloured_elements(adapter)
        await self._disable_transitions(adapter)
        coloured_image = await self._take_screenshot(adapter)
        await self._enable_transitions(adapter)

        detected_colours = await self.check_colors_brute_force(coloured_image)

        # remove the colours from coloured_elems that are not common between detected_colours and coloured_elems
        detected_coloured_elems = [
            elem for elem in coloured_elems if elem["color"] in detected_colours
        ]

        for elem in detected_coloured_elems:
            xpath = elem["xpath"]
            await self._hide_element(adapter, xpath)

        undetected_coloured_elems = [
            elem for elem in coloured_elems if elem["color"] not in detected_colours
        ]

        # re colour the undetected elements
        re_coloured_elems = await self._re_colour_elements(
            adapter, undetected_coloured_elems
        )

        # attempt to detect the missing elements after we have re coloured them
        await self._disable_transitions(adapter)
        re_coloured_image = await self._take_screenshot(adapter)
        await self._enable_transitions(adapter)

        new_detected_colours = await self.check_colors_brute_force(re_coloured_image)
        # new_expected_colours = [
        #     (elem['color'], int(elem['boundingBoxX']), int(elem['boundingBoxY']),
        #      int(elem['width']), int(elem['height']))
        #     for elem in re_coloured_elems
        # ]
        # new_detected_colours = await self._check_colours_(re_coloured_image, new_expected_colours)
        new_detected_coloured_elems = [
            elem for elem in re_coloured_elems if elem["color"] in new_detected_colours
        ]

        all_detected_coloured_elems = (
            detected_coloured_elems + new_detected_coloured_elems
        )

        # create the bounding boxes
        await self._create_text_bounding_boxes(adapter)
        document_dimensions_script = "return window.documentDimensions();"
        document_dimensions = await adapter.run_js(document_dimensions_script)
        document_width = document_dimensions["width"]
        document_height = document_dimensions["height"]

        annotations: ImageAnnotatorResponse = []
        fixed_top_annotations: ImageAnnotatorResponse = []
        fixed_bottom_annotations: ImageAnnotatorResponse = []
        seen_boxes = set()

        for elem in all_detected_coloured_elems:
            xpath = elem["xpath"]

            bounding_boxes_script = (
                f"return window.getElementBoundingBoxes({json.dumps(xpath)});"
            )
            bounding_boxes = await adapter.run_js(bounding_boxes_script)

            # create ImageAnnotation objects for each bounding box
            for i, box in enumerate(bounding_boxes):
                box_tuple = self.box_to_tuple(box)
                if box_tuple in seen_boxes:
                    continue
                seen_boxes.add(box_tuple)

                midpoint = (box["left"], box["top"] + box["height"])
                normalized_midpoint = (
                    midpoint[0] / document_width,
                    midpoint[1] / document_height,
                )

                if i == 0:
                    # First bounding box is handled differently
                    annotation_text = (
                        elem["idSymbol"] + " " + box["text"]
                        if (elem["idSymbol"] not in inserted_id_strings)
                        else box["text"]
                    )
                    tag_annotation = ImageAnnotation(
                        text=annotation_text,
                        midpoint=midpoint,
                        midpoint_normalized=normalized_midpoint,
                        width=box["width"] + 48,
                        height=box["height"],
                    )
                    if elem["isFixed"] and elem["fixedPosition"] == "top":
                        fixed_top_annotations.append(tag_annotation)
                    elif elem["isFixed"] and elem["fixedPosition"] == "bottom":
                        fixed_bottom_annotations.append(tag_annotation)
                    else:
                        annotations.append(tag_annotation)
                else:
                    annotation = ImageAnnotation(
                        text=box["text"],
                        midpoint=midpoint,
                        midpoint_normalized=normalized_midpoint,
                        width=box["width"],
                        height=box["height"],
                    )
                    if elem["isFixed"] and elem["fixedPosition"] == "top":
                        fixed_top_annotations.append(annotation)
                    elif elem["isFixed"] and elem["fixedPosition"] == "bottom":
                        fixed_bottom_annotations.append(annotation)
                    else:
                        annotations.append(annotation)

        # sort annotations before combining
        fixed_top_annotations = self.sort_annotations(fixed_top_annotations)
        annotations = self.sort_annotations(annotations)
        fixed_bottom_annotations = self.sort_annotations(fixed_bottom_annotations)

        combined_annotations = (
            fixed_top_annotations + annotations + fixed_bottom_annotations
        )

        annotations_formatted = format_text(combined_annotations)
        return annotations_formatted, tag_to_xpath

    @staticmethod
    def sort_annotations(annotations: ImageAnnotatorResponse) -> ImageAnnotatorResponse:
        return sorted(
            annotations,
            key=lambda x: (x["midpoint_normalized"][1], x["midpoint_normalized"][0]),
        )

    @staticmethod
    def box_to_tuple(box: BoundingBox) -> tuple[int, int, int, int]:
        return box["left"], box["top"], box["width"], box["height"]

    @staticmethod
    def combine_annotations(
        untagged_annotation: ImageAnnotatorResponse,
        tagged_annotation: ImageAnnotatorResponse,
    ) -> ImageAnnotatorResponse:
        combined_annotations: ImageAnnotatorResponse = (
            untagged_annotation + tagged_annotation
        )
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

    def _run_ocr(self, image: bytes) -> str:
        ocr_text = self._ocr_service.annotate(image)
        page_text = format_text(ocr_text)
        return page_text

    async def _tag_page(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> Dict[int, str]:
        await self._load_tarsier_utils(adapter)

        script = f"return window.tagifyWebpage({str(tag_text_elements).lower()});"
        tag_to_meta = await adapter.run_js(script)
        tag_to_xpath = {int(key): meta["xpath"] for key, meta in tag_to_meta.items()}
        return {int(key): value for key, value in tag_to_xpath.items()}

    async def _colour_based_tagify(
        self, adapter: BrowserAdapter, tag_text_elements: bool = False
    ) -> tuple[list[ColouredElem], set[str]]:
        await adapter.run_js(self._js_utils)

        script = f"return window.colourBasedTagify({str(tag_text_elements).lower()});"
        result = await adapter.run_js(script)
        colour_mapping = result["colorMapping"]
        inserted_id_strings = result["insertedIdStrings"]
        return colour_mapping, inserted_id_strings

    async def _remove_tags(self, adapter: BrowserAdapter) -> None:
        await self._load_tarsier_utils(adapter)
        script = "return window.removeTags();"

        await adapter.run_js(script)

    async def remove_tags(self, driver: AnyDriver) -> None:
        adapter = adapter_factory(driver)
        await self._remove_tags(adapter)

    async def _load_tarsier_utils(self, adapter: BrowserAdapter) -> None:
        await adapter.run_js(self._js_utils)

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
    async def check_colors_brute_force(image_bytes: bytes) -> list[str]:
        image = Image.open(BytesIO(image_bytes))
        image_rgb = image.convert("RGB")

        width, height = image_rgb.size
        unique_colors = set()

        # looping through each pixel
        for x in range(width):
            for y in range(height):
                color = image_rgb.getpixel((x, y))
                unique_colors.add(color)

        detected_colors_list = [f"rgb({r}, {g}, {b})" for r, g, b in unique_colors]  # type: ignore

        return detected_colors_list

    @staticmethod
    async def check_colors_targeted(
        image_bytes: bytes,
        expected_colours: list[Tuple[str, int, int, int, int]],
        threshold: int = 30,
    ) -> list[str]:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

        pixels = np.array(image)
        height, width, _ = pixels.shape

        detected_colours = set()

        for expected_color, box_x, box_y, box_width, box_height in expected_colours:
            # Ensure the bounding box is within the image dimensions
            box_x_end = min(box_x + box_width, width)
            box_y_end = min(box_y + box_height, height)

            # Extract the RGB value from the expected color string
            expected_rgb = tuple(map(int, expected_color[4:-1].split(",")))

            # Get the region of interest
            region = pixels[box_y:box_y_end, box_x:box_x_end]

            # Calculate the differences
            diff = np.abs(region - expected_rgb)

            # Check if any pixel is within the threshold
            within_threshold = np.all(diff <= threshold, axis=-1)

            if np.any(within_threshold):
                detected_colours.add(expected_color)

        return list(detected_colours)

    @staticmethod
    async def _hide_non_coloured_elements(adapter: BrowserAdapter) -> None:
        script = "return window.hideNonColouredElements();"
        await adapter.run_js(script)

    @staticmethod
    async def _create_text_bounding_boxes(adapter: BrowserAdapter) -> None:
        script = "return window.createTextBoundingBoxes();"
        await adapter.run_js(script)

    @staticmethod
    async def _hide_element(adapter: BrowserAdapter, xpath: str) -> None:
        safe_xpath = json.dumps(xpath)
        script = f"window.setElementVisibilityToHidden({safe_xpath});"
        await adapter.run_js(script)

    @staticmethod
    async def _re_colour_elements(
        adapter: BrowserAdapter, coloured_elems: list[ColouredElem]
    ) -> list[ColouredElem]:
        coloured_elems_json = json.dumps(coloured_elems)
        script = f"return window.reColourElements({coloured_elems_json});"
        updated_coloured_elems = await adapter.run_js(script)

        return updated_coloured_elems

    @staticmethod
    async def _disable_transitions(adapter: BrowserAdapter) -> None:
        script = "window.disableTransitionsAndAnimations();"
        await adapter.run_js(script)

    @staticmethod
    async def _enable_transitions(adapter: BrowserAdapter) -> None:
        script = "window.enableTransitionsAndAnimations();"
        await adapter.run_js(script)
