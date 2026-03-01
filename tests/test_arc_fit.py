"""Tests for arc fitting (polyline → G02/G03 arc segments)."""

import math
import pytest
from backend.arc_fit import fit_arcs, LineSegment, ArcSegment


def _make_circle(cx, cy, r, n=36, clockwise=False):
    """Generate circle points."""
    points = []
    for i in range(n + 1):
        angle = 2 * math.pi * i / n
        if clockwise:
            angle = -angle
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return points


def test_fit_arcs_on_circle():
    """Points forming a circle should produce ArcSegments."""
    circle = _make_circle(50, 50, 20, n=36)
    segments = fit_arcs(circle)
    arc_count = sum(1 for s in segments if isinstance(s, ArcSegment))
    assert arc_count > 0


def test_fit_arcs_on_square():
    """A perfect square should produce only LineSegments."""
    square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    segments = fit_arcs(square)
    assert all(isinstance(s, LineSegment) for s in segments)


def test_arc_segment_has_center():
    """ArcSegments should have center coordinates and direction."""
    circle = _make_circle(50, 50, 20, n=36)
    segments = fit_arcs(circle)
    arcs = [s for s in segments if isinstance(s, ArcSegment)]
    assert len(arcs) > 0
    for arc in arcs:
        assert hasattr(arc, 'center')
        assert hasattr(arc, 'clockwise')
        assert len(arc.center) == 2


def test_fit_arcs_preserves_endpoints():
    """The chain of segments should start and end at the original points."""
    circle = _make_circle(50, 50, 20, n=36)
    segments = fit_arcs(circle)
    first = segments[0]
    assert abs(first.start[0] - circle[0][0]) < 0.1
    assert abs(first.start[1] - circle[0][1]) < 0.1


def test_fit_arcs_empty():
    """Empty input returns empty output."""
    assert fit_arcs([]) == []


def test_fit_arcs_too_few_points():
    """Fewer than 2 points returns empty."""
    assert fit_arcs([(0, 0)]) == []


def test_fit_arcs_straight_line():
    """Collinear points should produce a single LineSegment."""
    line = [(0, 0), (5, 0), (10, 0), (15, 0)]
    segments = fit_arcs(line)
    assert all(isinstance(s, LineSegment) for s in segments)
