from enum import Enum

import cv2
import numpy as np


class ImageType(Enum):
    LINE_ART = "line_art"
    PHOTO = "photo"


def classify_image(img: np.ndarray) -> ImageType:
    """Classify an image as line art or photo based on intensity distribution.

    Line art has a bimodal distribution (mostly black and white pixels).
    Photos have a spread distribution across the intensity range.
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    total_pixels = gray.size
    near_black = np.sum(gray < 51)   # within 20% of 0
    near_white = np.sum(gray > 204)  # within 20% of 255
    extreme_ratio = (near_black + near_white) / total_pixels

    if extreme_ratio > 0.7:
        return ImageType.LINE_ART
    return ImageType.PHOTO
