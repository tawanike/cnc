import numpy as np
from backend.classify import classify_image, ImageType


def test_classify_lineart():
    """A bimodal image (mostly black and white) should be classified as line art."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    assert classify_image(img) == ImageType.LINE_ART


def test_classify_photo():
    """An image with spread intensity distribution should be classified as photo."""
    rng = np.random.default_rng(42)
    img = rng.integers(50, 200, size=(100, 100), dtype=np.uint8)
    assert classify_image(img) == ImageType.PHOTO


def test_classify_already_grayscale():
    """Should handle both grayscale and color input."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    assert classify_image(img) == ImageType.LINE_ART
