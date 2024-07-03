from abc import ABC, abstractmethod
from typing import Any, Dict, Literal

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from google.cloud import vision

from tarsier.ocr.types import ImageAnnotatorResponse, ImageAnnotation

OCRProvider = Literal["google", "microsoft"]


class OCRService(ABC):
    def __init__(self, ocr_provider: OCRProvider):
        self.ocr_provider = ocr_provider

    @abstractmethod
    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        pass


class GoogleVisionOCRService(OCRService):
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("google")

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
            return []

        whole_text_box_max = annotations[0].bounding_poly.vertices[2]
        max_width = whole_text_box_max.x
        max_height = whole_text_box_max.y

        annotations_normed: list[ImageAnnotation] = []
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
                    "width": box[1].x - box[0].x,
                    "height": box[2].y - box[0].y,
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

        return annotations_normed


class MicrosoftAzureOCRService(OCRService):
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("microsoft")

        try:
            self.client = ImageAnalysisClient(
                endpoint=credentials["endpoint"],
                credential=AzureKeyCredential(credentials["key"]),
            )
        except Exception:  # TODO: specify exception
            raise ValueError(
                "OCR client creation from credentials failed.\n"
                "Your microsoft azure vision credentials can be created here:\n"
                "https://learn.microsoft.com/en-us/python/api/overview/azure/cognitive-services?view=azure-python-preview"
            )

    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        result = self.client.analyze(
            image_data=image_file, visual_features=[VisualFeatures.READ]
        )

        if result.read is None:
            return []

        max_width, max_height = 0, 0
        for line in result.read.blocks[0].lines:
            for word in line.words:
                max_width = max(
                    [max_width, word.bounding_polygon[1].x, word.bounding_polygon[2].x]
                )
                max_height = max(
                    [max_height, word.bounding_polygon[2].y, word.bounding_polygon[3].y]
                )

        annotations_normed: list[ImageAnnotation] = []
        for line in result.read.blocks[0].lines:
            for word in line.words:
                xmin = min([word.bounding_polygon[0].x, word.bounding_polygon[3].x])
                xmax = max([word.bounding_polygon[1].x, word.bounding_polygon[2].x])
                ymin = min([word.bounding_polygon[0].y, word.bounding_polygon[1].y])
                ymax = max([word.bounding_polygon[2].y, word.bounding_polygon[3].y])

                # NOTE: we now use the bottom left coordinate as the "midpoint"
                midpoint = (xmin, ymax)

                annotations_normed.append(
                    {
                        "text": word.text,
                        "midpoint": midpoint,
                        "midpoint_normalized": (
                            midpoint[0] / max_width,
                            midpoint[1] / max_height,
                        ),
                        "width": xmax - xmin,
                        "height": ymax - ymin,
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

        return annotations_normed
