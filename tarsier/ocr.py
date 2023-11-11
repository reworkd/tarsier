from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, List
from collections import defaultdict
import math
from pydantic import BaseModel
from google.cloud import vision


class ImageAnnotation(BaseModel):
    text: str  # the word
    midpoint: Tuple[float, float]  # the UNNORMALIZED midpoint of the word, (X,Y)
    midpoint_normalized: Tuple[
        float, float
    ]  # the normalized midpoint between 0 - 1  (X,Y)


class ImageAnnotatorResponse(BaseModel):
    words: List[ImageAnnotation]  # a list of words and their midpoints


class OCRService(ABC):
    @abstractmethod
    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        pass

    def format_text(self, ocr_text: ImageAnnotatorResponse) -> str:
        # Initialize dimensions
        canvas_width = 200
        canvas_height = 100

        # Cluster tokens by line
        line_cluster = defaultdict(list)
        for annotation in ocr_text.words:
            # y = math.floor(annotation.midpoint_normalized[1] * canvas_height)
            y = round(annotation.midpoint_normalized[1], 3)
            line_cluster[y].append(annotation)
        canvas_height = max(canvas_height, len(line_cluster))

        # find max line length
        max_line_length = max(
            sum([len(token.text) + 1 for token in line])
            for line in line_cluster.values()
        )
        canvas_width = max(canvas_width, max_line_length)

        # Create an empty canvas (list of lists filled with spaces)
        canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

        # Place the annotations on the canvas
        for i, (y, line_annotations) in enumerate(line_cluster.items()):
            # Sort annotations in this line by x coordinate
            line_annotations.sort(key=lambda x: x.midpoint_normalized[0])

            last_x = 0  # Keep track of the last position where text was inserted
            for annotation in line_annotations:
                x = math.floor(annotation.midpoint_normalized[0] * canvas_width)

                # Move forward if there's an overlap
                x = max(x, last_x)

                # Check if the text fits; if not, move to next line (this is simplistic)
                if x + len(annotation.text) >= canvas_width:
                    continue  # TODO: extend the canvas_width in this case

                # Place the text on the canvas
                for j, char in enumerate(annotation.text):
                    canvas[i][x + j] = char

                # Update the last inserted position
                last_x = x + len(annotation.text) + 1  # +1 for a space between words

        # Delete all whitespace characters after the last non-whitespace character in each row
        canvas = [list("".join(row).rstrip()) for row in canvas]

        # Convert the canvas to a plaintext string
        page_text = "\n".join("".join(row) for row in canvas)
        page_text = page_text.strip()
        page_text = "-" * canvas_width + "\n" + page_text + "\n" + "-" * canvas_width
        page_text = page_text.replace("        ", "\t")

        return page_text


class GoogleVisionOCRService(OCRService):
    def __init__(self, credentials: Dict[str, Any]):
        try:
            self.client = vision.ImageAnnotatorClient.from_service_account_info(
                credentials
            )
        except Exception:  # TODO: specify exception
            raise ValueError("OCR client creation from credentials failed.")

        self._features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]

    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        image = vision.Image(content=image_file)
        request = vision.AnnotateImageRequest(image=image, features=self._features)
        res = self.client.annotate_image(request)  # TODO: make this async?

        annotations = res.text_annotations
        whole_text_box_max = annotations[0].bounding_poly.vertices[2]
        max_width = whole_text_box_max.x
        max_height = whole_text_box_max.y

        annotations_normed = []
        for text in annotations[1:]:
            box = text.bounding_poly.vertices

            # midpoint: average position betwen
            # the upper left location and lower
            # right position
            midpoint = ((box[2].x + box[0].x) / 2, (box[2].y + box[0].y) / 2)

            annotations_normed.append(
                ImageAnnotation(
                    text=text.description,
                    midpoint=midpoint,
                    midpoint_normalized=(
                        midpoint[0] / max_width,
                        midpoint[1] / max_height,
                    ),
                )
            )

        annotations_normed = list(
            sorted(
                annotations_normed,
                key=lambda x: (x.midpoint_normalized[1], x.midpoint_normalized[0]),
            )
        )
        response = ImageAnnotatorResponse(
            words=annotations_normed,
        )

        return response
