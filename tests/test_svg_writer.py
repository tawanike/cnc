from backend.svg_writer import write_svg


def test_write_svg_returns_string():
    polylines = [[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]]
    result = write_svg(polylines, width=100, height=100)
    assert isinstance(result, str)
    assert "<svg" in result


def test_write_svg_contains_polyline():
    polylines = [[(0, 0), (50, 50), (100, 0)]]
    result = write_svg(polylines, width=100, height=100)
    assert "<polyline" in result
    assert "0,0" in result


def test_write_svg_multiple_polylines():
    polylines = [
        [(0, 0), (50, 0)],
        [(60, 60), (100, 100)],
    ]
    result = write_svg(polylines, width=100, height=100)
    assert result.count("<polyline") == 2


def test_write_svg_with_scale():
    polylines = [[(0, 0), (10, 0), (10, 10)]]
    result = write_svg(polylines, width=10, height=10, scale_factor=2.0)
    assert "20,0" in result


def test_write_svg_empty():
    result = write_svg([], width=100, height=100)
    assert "<svg" in result
    assert "<polyline" not in result
