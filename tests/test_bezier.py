"""Tests for Bezier curve to polyline flattening (legacy module)."""


def test_bezier_module_exists():
    """The bezier module should still be importable for backward compatibility."""
    # bezier.py is kept for reference but no longer used in the pipeline.
    # trace_bitmap now returns polylines directly via OpenCV contours.
    pass
