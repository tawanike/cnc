from backend.pipeline import convert_image, preview_image


def test_convert_image_returns_dxf_bytes(test_png_bytes):
    result = convert_image(test_png_bytes, "test.png")
    assert isinstance(result, bytes)
    assert b"LWPOLYLINE" in result


def test_convert_image_with_target_width(test_png_bytes):
    result = convert_image(test_png_bytes, "test.png", target_width_mm=200.0)
    assert isinstance(result, bytes)


def test_preview_image_returns_svg_and_stats(test_png_bytes):
    result = preview_image(test_png_bytes, "test.png")
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
