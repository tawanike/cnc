import numpy as np
from backend.trace import trace_bitmap


def test_trace_returns_polylines():
    """Tracing a simple shape should return at least one polyline."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    polylines = trace_bitmap(bitmap)
    assert len(polylines) > 0


def test_trace_polyline_has_points():
    """Each polyline should have multiple (x, y) tuple points."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    polylines = trace_bitmap(bitmap)
    for pl in polylines:
        assert len(pl) >= 2
        for pt in pl:
            assert len(pt) == 2


def test_trace_contour_is_closed():
    """Contours should be closed (first point equals last point)."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    polylines = trace_bitmap(bitmap)
    for pl in polylines:
        assert pl[0] == pl[-1]


def test_trace_empty_image_returns_no_paths():
    """An all-white image should return no paths."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    polylines = trace_bitmap(bitmap)
    assert len(polylines) == 0


def test_trace_multiple_shapes():
    """Multiple separated shapes should produce multiple polylines."""
    bitmap = np.ones((200, 200), dtype=np.uint8) * 255
    bitmap[10:40, 10:40] = 0     # top-left square
    bitmap[160:190, 160:190] = 0  # bottom-right square
    polylines = trace_bitmap(bitmap)
    assert len(polylines) >= 2


def test_trace_points_within_image_bounds():
    """All traced points should be within the image dimensions."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    polylines = trace_bitmap(bitmap)
    for pl in polylines:
        for x, y in pl:
            assert 0 <= x <= 100
            assert 0 <= y <= 100
