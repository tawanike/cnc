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


def test_convert_image_nc_format(test_png_bytes):
    """Pipeline should produce NC output when format='nc'."""
    from backend.pipeline import convert_image
    result = convert_image(test_png_bytes, "test.png", output_format="nc")
    assert isinstance(result, bytes)
    text = result.decode()
    assert "G21" in text
    assert "M30" in text


def test_convert_image_nc_with_params(test_png_bytes):
    """NC output should respect custom cutting params."""
    from backend.pipeline import convert_image
    from backend.nc_writer import CuttingParams
    params = CuttingParams(feed_rate=2000, safe_z=15.0)
    result = convert_image(
        test_png_bytes, "test.png", output_format="nc", cutting_params=params,
    )
    text = result.decode()
    assert "F2000" in text
    assert "Z15.0000" in text


def test_convert_image_dxf_default(test_png_bytes):
    """Default format should still be DXF."""
    from backend.pipeline import convert_image
    result = convert_image(test_png_bytes, "test.png")
    assert b"SECTION" in result
