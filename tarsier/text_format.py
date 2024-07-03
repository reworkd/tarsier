import math
import statistics
from collections import defaultdict
from typing import Dict, List

from tarsier.ocr import ImageAnnotatorResponse
from tarsier.ocr.types import ImageAnnotation


def format_text(ocr_text: ImageAnnotatorResponse) -> str:
    # Cluster tokens by line
    line_cluster: Dict[float, List[ImageAnnotation]] = defaultdict(list)
    for annotation in ocr_text:
        if (
            len(line_cluster.keys())
            and abs(annotation["midpoint"][1] - list(line_cluster.keys())[-1]) < 10
        ):  # within 10px of the last line
            line_cluster[list(line_cluster.keys())[-1]].append(annotation)
        else:
            line_cluster[annotation["midpoint"][1]].append(annotation)
    canvas_height = len(line_cluster)

    default_canvas_width = 80  # Default canvas width

    # Ensure line_cluster is not empty before proceeding
    if line_cluster:
        canvas_width = int(
            max(
                [
                    max(
                        (
                            sum(len(token["text"]) + 1 for token in line)
                            for line in line_cluster.values()
                        ),
                        default=default_canvas_width,
                    ),
                    max(
                        (
                            canvas_height
                            * (
                                annotation["midpoint"][0]
                                / annotation["midpoint_normalized"][0]
                                if annotation["midpoint_normalized"][0] != 0
                                else default_canvas_width
                            )
                            / (
                                annotation["midpoint"][1]
                                / annotation["midpoint_normalized"][1]
                                if annotation["midpoint_normalized"][1] != 0
                                else default_canvas_width
                            )
                            for line in line_cluster.values()
                            for annotation in line
                        ),
                        default=default_canvas_width,
                    ),
                    max(
                        (
                            max(
                                (
                                    len(annotation["text"])
                                    / (1 - annotation["midpoint_normalized"][0])
                                    if annotation["midpoint_normalized"][0] != 1
                                    else len(annotation["text"])
                                )
                                for annotation in line
                            )
                            for line in line_cluster.values()
                        ),
                        default=default_canvas_width,
                    ),
                ]
            )
        )
    else:
        canvas_width = default_canvas_width

    # Create an empty canvas (list of lists filled with spaces)
    canvas = [[" " for _ in range(canvas_width)] for _ in range(canvas_height)]

    letter_height = 30
    empty_space_height = letter_height + 5
    max_previous_line_height = empty_space_height

    # Place the annotations on the canvas
    i = 0
    for y, line_annotations in line_cluster.items():
        # Sort annotations in this line by x coordinate
        line_annotations.sort(key=lambda e: e["midpoint_normalized"][0])
        # grouped_line_annotations = line_annotations
        grouped_line_annotations = group_words_in_sentence(line_annotations)

        # Use the TOP height of the letter
        max_line_height = max(
            annotation["midpoint"][1] - annotation["height"]
            for annotation in grouped_line_annotations
        )
        height_to_add = math.floor(
            (max_line_height - max_previous_line_height) // empty_space_height
        )
        if height_to_add > 0:
            for _ in range(height_to_add):
                canvas.append([" " for _ in range(canvas_width)])
                i += 1

        # Store the BOTTOM height of the letter. In doing this, we can compare the bottom of the previous line
        # with the top of the current line. This is to avoid issues with larger font
        max_previous_line_height = int(
            max(annotation["midpoint"][1] for annotation in grouped_line_annotations)
        )

        last_x = 0
        for annotation in grouped_line_annotations:
            text = annotation["text"]

            x = math.floor(annotation["midpoint_normalized"][0] * canvas_width)

            # Move forward if there's an overlap
            x = max(x, last_x)

            # Check if the text fits; if not, move to next line (this is simplistic)
            if x + len(text) >= canvas_width:
                canvas[i] += [" " for _ in range(len(text) + 1)]

            # Place the text on the canvas
            for j, char in enumerate(text):
                canvas[i][x + j] = char

            # Update the last inserted position
            last_x = x + len(text) + 1  # +1 for a space between words

        i += 1

    # Delete all whitespace characters after the last non-whitespace character in each row
    canvas = [list("".join(row).rstrip()) for row in canvas]

    # Convert the canvas to a plaintext string
    page_text = "\n".join("".join(row) for row in canvas)
    page_text = page_text.strip()

    page_text = "-" * canvas_width + "\n" + page_text + "\n" + "-" * canvas_width

    return page_text


def group_words_in_sentence(
    line_annotations: List[ImageAnnotation],
) -> List[ImageAnnotation]:
    """
    Issue: Large text will contain large spaces in between words after text formatting because of how we render them
        into plaintext. This is because the rendered font size is much smaller than the actual font size in page space.
        When we insert text, we calculate the insert position as the max between the last inserted character in text
        space and the new characters midpoint.

    This Solution: Preprocess the line to group large words together in the same line. This works by calculating the
        width of a single character for the current font size. If the next word is of a similar font_size and is within
         a space of the previous word, we assume they are a part of the same group and combine them together.
    """

    grouped_annotations: List[ImageAnnotation] = []
    current_group: List[ImageAnnotation] = []

    for annotation in line_annotations:
        if len(current_group) == 0:
            current_group.append(annotation)
            continue
        padding = 2
        character_width = (
            current_group[-1]["width"] / len(current_group[-1]["text"])
        ) * padding  # Additional padding
        is_single_character_away = annotation["midpoint"][0] <= (
            (current_group[-1]["midpoint"][0] + current_group[-1]["width"])
            + character_width
        )

        if (
            abs(annotation["height"] - current_group[0]["height"]) <= 4
            and is_single_character_away
        ):
            current_group.append(annotation)
        else:
            if len(current_group) > 0:
                grouped_annotation = create_grouped_annotation(current_group)
                grouped_annotations.append(grouped_annotation)
                current_group = [annotation]

    # Append the last group if it exists
    if current_group:
        grouped_annotations.append(create_grouped_annotation(current_group))

    return grouped_annotations


def create_grouped_annotation(group: List[ImageAnnotation]) -> ImageAnnotation:
    # For the text, don't put a space if it is a period or a comma or a quote
    text = ""

    for word in group:
        if word["text"] in [".", ",", '"', "'", ":", ";", "!", "?", "{", "}", "’", "”"]:
            text += word["text"]
        else:
            text += " " + word["text"] if text != "" else word["text"]

    # Test that the 'word' is longer than 1 character and contains alphabetical or numerical characters
    is_word = any(char.isalnum() for char in text)
    if is_word and statistics.median([word["height"] for word in group]) > 25:
        text = "**" + text + "**"

    return {
        "text": text,
        "midpoint": (
            group[0]["midpoint"][0],
            group[0]["midpoint"][1],
        ),
        "midpoint_normalized": (
            group[0]["midpoint_normalized"][0],
            group[0]["midpoint_normalized"][1],
        ),
        "width": sum(a["width"] for a in group),
        "height": group[0]["height"],
    }
