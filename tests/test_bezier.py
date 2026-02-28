"""Tests for Bezier curve to polyline flattening."""

import math
from backend.trace import Point, BezierSegment, TracedPath
from backend.bezier import flatten_paths


def test_flatten_straight_line():
    """A 'bezier' that is actually a straight line should produce minimal points."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(33, 0), c2=Point(66, 0), end_point=Point(100, 0),
                is_corner=False,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    assert polylines[0][0] == (0.0, 0.0)
    assert polylines[0][-1] == (100.0, 0.0)


def test_flatten_curve_produces_multiple_points():
    """A real curve should produce multiple intermediate points."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(0, 100), c2=Point(100, 100), end_point=Point(100, 0),
                is_corner=False,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    assert len(polylines[0]) > 2


def test_flatten_corner_segment():
    """A corner segment should produce line segments."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(50, 0), c2=Point(50, 0), end_point=Point(50, 50),
                is_corner=True,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    assert (0.0, 0.0) in polylines[0]
    assert (50.0, 0.0) in polylines[0]
    assert (50.0, 50.0) in polylines[0]


def test_flatten_empty():
    """Empty input should return empty output."""
    assert flatten_paths([], tolerance=0.1) == []
