import io

import numpy as np
from PIL import Image
import pytest


@pytest.fixture
def test_png_bytes() -> bytes:
    """Create a simple black-square-on-white PNG for testing."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()
