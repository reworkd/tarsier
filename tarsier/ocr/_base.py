import math
from abc import ABC, abstractmethod
from collections import defaultdict

from tarsier.ocr.types import ImageAnnotatorResponse


class OCRService(ABC):
    @abstractmethod
    def annotate(self, image_file: bytes) -> ImageAnnotatorResponse:
        pass

    @staticmethod
    def format_text(ocr_text: ImageAnnotatorResponse) -> str:
        # Initialize dimensions
        canvas_width = 200
        canvas_height = 100

        # Cluster tokens by line
        line_cluster = defaultdict(list)
        for annotation in ocr_text["words"]:
            # y = math.floor(annotation.midpoint_normalized[1] * canvas_height)
            y = round(annotation["midpoint_normalized"][1], 3)
            line_cluster[y].append(annotation)
        canvas_height = max(canvas_height, len(line_cluster))

        # find max line length
        max_line_length = max(
            sum([len(token["text"]) + 1 for token in line])
            for line in line_cluster.values()
        )
        canvas_width = max(canvas_width, max_line_length)

        # Create an empty canvas (list of lists filled with spaces)
        canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

        # Place the annotations on the canvas
        for i, (y, line_annotations) in enumerate(line_cluster.items()):
            # Sort annotations in this line by x coordinate
            line_annotations.sort(key=lambda e: e["midpoint_normalized"][0])

            last_x = 0  # Keep track of the last position where text was inserted
            for annotation in line_annotations:
                text = annotation["text"]

                x = math.floor(annotation["midpoint_normalized"][0] * canvas_width)

                # Move forward if there's an overlap
                x = max(x, last_x)

                # Check if the text fits; if not, move to next line (this is simplistic)
                if x + len(text) >= canvas_width:
                    continue  # TODO: extend the canvas_width in this case

                # Place the text on the canvas
                for j, char in enumerate(text):
                    canvas[i][x + j] = char

                # Update the last inserted position
                last_x = x + len(text) + 1  # +1 for a space between words

        # Delete all whitespace characters after the last non-whitespace character in each row
        canvas = [list("".join(row).rstrip()) for row in canvas]

        # Convert the canvas to a plaintext string
        page_text = "\n".join("".join(row) for row in canvas)
        page_text = page_text.strip()
        page_text = "-" * canvas_width + "\n" + page_text + "\n" + "-" * canvas_width
        page_text = page_text.replace("        ", "\t")

        return page_text
