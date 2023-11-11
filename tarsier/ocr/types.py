from typing import List, Tuple, TypedDict


class ImageAnnotation(TypedDict):
    text: str  # the word
    midpoint: Tuple[float, float]  # the UNNORMALIZED midpoint of the word, (X,Y)
    midpoint_normalized: Tuple[
        float, float
    ]  # the normalized midpoint between 0 - 1  (X,Y)


class ImageAnnotatorResponse(TypedDict):
    words: List[ImageAnnotation]  # a list of words and their midpoints
