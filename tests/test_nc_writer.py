"""Tests for NC (G-code) file writer."""

import pytest
from backend.nc_writer import write_nc, CuttingParams
from backend.arc_fit import LineSegment, ArcSegment


def _make_square_segments():
    """Simple square as line segments."""
    return [
        LineSegment((0, 0), (10, 0)),
        LineSegment((10, 0), (10, 10)),
        LineSegment((10, 10), (0, 10)),
        LineSegment((0, 10), (0, 0)),
    ]


def test_write_nc_returns_bytes():
    segments_per_shape = [_make_square_segments()]
    result = write_nc(segments_per_shape)
    assert isinstance(result, bytes)


def test_write_nc_header():
    result = write_nc([_make_square_segments()]).decode()
    assert "G21" in result
    assert "G40" in result
    assert "G90" in result


def test_write_nc_footer():
    result = write_nc([_make_square_segments()]).decode()
    lines = result.strip().split("\n")
    assert "M30" in lines[-1]


def test_write_nc_torch_on_off():
    result = write_nc([_make_square_segments()]).decode()
    assert result.count("M08") == 1
    assert result.count("M09") >= 1


def test_write_nc_line_numbers():
    result = write_nc([_make_square_segments()]).decode()
    for line in result.strip().split("\n"):
        assert line.startswith("N"), f"Line missing N-number: {line}"


def test_write_nc_dwell():
    result = write_nc([_make_square_segments()]).decode()
    assert "G04 P" in result


def test_write_nc_safe_z_retract():
    params = CuttingParams(safe_z=10.0)
    result = write_nc([_make_square_segments()], params).decode()
    assert "Z10.0000" in result


def test_write_nc_custom_params():
    params = CuttingParams(feed_rate=2000, pierce_feed=50, cut_z=2.0)
    result = write_nc([_make_square_segments()], params).decode()
    assert "F2000" in result
    assert "F50" in result
    assert "Z2.0000" in result


def test_write_nc_arc_segment():
    arc = ArcSegment(
        start=(10, 0), end=(0, 10), center=(0, 0), clockwise=True,
    )
    result = write_nc([[arc]]).decode()
    assert "G02" in result or "G03" in result


def test_write_nc_multiple_shapes():
    shapes = [_make_square_segments(), _make_square_segments()]
    result = write_nc(shapes).decode()
    assert result.count("M08") == 2
    assert result.count("M09") >= 2


def test_write_nc_empty():
    result = write_nc([]).decode()
    assert "G21" in result
    assert "M30" in result
