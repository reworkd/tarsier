import io
from typing import List

from PIL import Image


def stitch_screenshots_in_memory(images: List[Image.Image]) -> bytes:
    total_width = max(image.width for image in images)
    total_height = sum(image.height for image in images)
    stitched_image = Image.new("RGB", (total_width, total_height)) 

    y_offset = 0
    for img in images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.height

    img_byte_arr = io.BytesIO()
    stitched_image.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()
