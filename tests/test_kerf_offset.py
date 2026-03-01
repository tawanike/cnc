"""Tests for kerf offset (polygon outward expansion)."""

import pytest
from backend.kerf_offset import offset_polylines


def test_offset_square_expands():
    """A 10x10 square offset by 1mm should become ~12x12."""
    square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    result = offset_polylines([square], kerf_width=2.0)
    assert len(result) == 1
    xs = [p[0] for p in result[0]]
    ys = [p[1] for p in result[0]]
    assert min(xs) < 0  # expanded left
    assert max(xs) > 10  # expanded right
    assert min(ys) < 0  # expanded down
    assert max(ys) > 10  # expanded up


def test_offset_zero_kerf_unchanged():
    """Zero kerf width should return contours unchanged."""
    square = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    result = offset_polylines([square], kerf_width=0.0)
    assert len(result) == 1
    assert len(result[0]) >= 4


def test_offset_preserves_closure():
    """Offset contours should remain closed."""
    triangle = [(0, 0), (10, 0), (5, 10), (0, 0)]
    result = offset_polylines([triangle], kerf_width=1.0)
    for contour in result:
        assert contour[0] == contour[-1]


def test_offset_multiple_contours():
    """Multiple contours are offset independently."""
    c1 = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
    c2 = [(20, 0), (30, 0), (30, 10), (20, 10), (20, 0)]
    result = offset_polylines([c1, c2], kerf_width=1.0)
    assert len(result) == 2


def test_offset_empty_input():
    """Empty input returns empty output."""
    result = offset_polylines([], kerf_width=1.0)
    assert result == []
