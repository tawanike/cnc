import numpy as np
from backend.classify import ImageType
from backend.preprocess import preprocess_image


def test_preprocess_lineart_returns_binary():
    """Line art preprocessing should return a binary image (only 0 and 255)."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    result = preprocess_image(img, ImageType.LINE_ART)
    unique_values = set(np.unique(result))
    assert unique_values.issubset({0, 255})


def test_preprocess_photo_returns_binary():
    """Photo preprocessing should return a binary image."""
    rng = np.random.default_rng(42)
    img = np.zeros((100, 100), dtype=np.uint8)
    img[25:75, 25:75] = 180
    img = img + rng.integers(0, 30, size=(100, 100), dtype=np.uint8)
    result = preprocess_image(img, ImageType.PHOTO)
    unique_values = set(np.unique(result))
    assert unique_values.issubset({0, 255})


def test_preprocess_output_shape():
    """Output should be 2D regardless of input."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    result = preprocess_image(img, ImageType.LINE_ART)
    assert len(result.shape) == 2


def test_preprocess_preserves_content():
    """Preprocessing should not destroy the main shape."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[30:70, 30:70] = 0
    result = preprocess_image(img, ImageType.LINE_ART)
    assert result[50, 50] == 0
    assert result[5, 5] == 255
