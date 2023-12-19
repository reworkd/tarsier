from typing import Any, Dict

from google.cloud import vision

from tarsier.ocr._base import OCRService
from tarsier.ocr.types import ImageAnnotatorResponse


class GoogleVisionOCRService(OCRService):
    def __init__(self, credentials: Dict[str, Any]):
        try:
            self.client = vision.ImageAnnotatorClient.from_service_account_info(
                credentials
            )
        except Exception:  # TODO: specify exception
            raise ValueError(
                "OCR client creation from credentials failed.\n"
                "Google your google cloud vision credentials can be created here:\n"
                "https://console.cloud.google.com/apis/api/vision.googleapis.com"
            )

        text_detection = vision.Feature()
        text_detection.type_ = vision.Feature.Type.TEXT_DETECTION  # type: ignore
        self._features = [text_detection]

    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        image = vision.Image()
        image.content = image_file

        request = vision.AnnotateImageRequest()
        request.image = image
        request.features = self._features

        res = self.client.annotate_image(request)  # TODO: make this async?

        annotations = res.text_annotations
        if len(annotations) == 0:
            return {"words": []}

        whole_text_box_max = annotations[0].bounding_poly.vertices[2]
        max_width = whole_text_box_max.x
        max_height = whole_text_box_max.y

        annotations_normed = []
        for text in annotations[1:]:
            box = text.bounding_poly.vertices

            # NOTE: we now use the bottom left coordinate as the "midpoint"
            midpoint = (box[3].x, box[3].y)

            annotations_normed.append(
                {
                    "text": text.description,
                    "midpoint": midpoint,
                    "midpoint_normalized": (
                        midpoint[0] / max_width,
                        midpoint[1] / max_height,
                    ),
                }
            )

        annotations_normed = list(
            sorted(
                annotations_normed,
                key=lambda x: (
                    x["midpoint_normalized"][1],
                    x["midpoint_normalized"][0],
                ),
            )
        )

        return {"words": annotations_normed}  # type: ignore
