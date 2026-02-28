import numpy as np
from backend.trace import trace_bitmap, TracedPath


def test_trace_returns_paths():
    """Tracing a simple shape should return at least one path."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    paths = trace_bitmap(bitmap)
    assert len(paths) > 0


def test_traced_path_has_segments():
    """Each path should have a start point and segments."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    paths = trace_bitmap(bitmap)
    for path in paths:
        assert path.start_point is not None
        assert len(path.segments) > 0


def test_trace_empty_image_returns_no_paths():
    """An all-white image should return no paths."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    paths = trace_bitmap(bitmap)
    assert len(paths) == 0
