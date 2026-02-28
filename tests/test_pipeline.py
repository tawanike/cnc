import numpy as np
from PIL import Image
import io

from backend.pipeline import convert_image, preview_image


def _make_test_png() -> bytes:
    """Create a simple black-square-on-white PNG."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


def test_convert_image_returns_dxf_bytes():
    png_bytes = _make_test_png()
    result = convert_image(png_bytes, "test.png")
    assert isinstance(result, bytes)
    assert b"LWPOLYLINE" in result


def test_convert_image_with_target_width():
    png_bytes = _make_test_png()
    result = convert_image(png_bytes, "test.png", target_width_mm=200.0)
    assert isinstance(result, bytes)


def test_preview_image_returns_svg_and_stats():
    png_bytes = _make_test_png()
    result = preview_image(png_bytes, "test.png")
    assert "svg" in result
    assert "<svg" in result["svg"]
    assert "stats" in result
    assert "path_count" in result["stats"]
    assert "width_mm" in result["stats"]
    assert "height_mm" in result["stats"]


def test_convert_image_invalid_format():
    """Non-image bytes should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="decode"):
        convert_image(b"not an image", "bad.png")
