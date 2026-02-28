"""Bezier curve to polyline flattening using recursive De Casteljau subdivision.

This module is kept for reference but is no longer used in the pipeline.
The trace module now returns polylines directly via OpenCV contours.
"""

from dataclasses import dataclass


@dataclass
class Point:
    """A 2D point."""
    x: float
    y: float


@dataclass
class BezierSegment:
    """A cubic Bezier curve segment or corner segment."""
    c1: Point
    c2: Point
    end_point: Point
    is_corner: bool


@dataclass
class TracedPath:
    """A traced path consisting of a start point and a sequence of segments."""
    start_point: Point
    segments: list[BezierSegment]


def _subdivide_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    tolerance: float,
    points: list[tuple[float, float]],
) -> None:
    """Recursively subdivide a cubic Bezier curve into line segments."""
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    d2 = abs((p1[0] - p3[0]) * dy - (p1[1] - p3[1]) * dx)
    d3 = abs((p2[0] - p3[0]) * dy - (p2[1] - p3[1]) * dx)

    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        points.append(p3)
        return

    if (d2 + d3) ** 2 <= tolerance * tolerance * length_sq:
        points.append(p3)
        return

    m01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    m12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    m23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
    m012 = ((m01[0] + m12[0]) / 2, (m01[1] + m12[1]) / 2)
    m123 = ((m12[0] + m23[0]) / 2, (m12[1] + m23[1]) / 2)
    mid = ((m012[0] + m123[0]) / 2, (m012[1] + m123[1]) / 2)

    _subdivide_bezier(p0, m01, m012, mid, tolerance, points)
    _subdivide_bezier(mid, m123, m23, p3, tolerance, points)


def flatten_paths(
    paths: list[TracedPath], tolerance: float = 0.1
) -> list[list[tuple[float, float]]]:
    """Convert Bezier curve paths to polylines."""
    polylines: list[list[tuple[float, float]]] = []

    for path in paths:
        points: list[tuple[float, float]] = [(path.start_point.x, path.start_point.y)]
        current = (path.start_point.x, path.start_point.y)

        for seg in path.segments:
            if seg.is_corner:
                corner = (seg.c1.x, seg.c1.y)
                end = (seg.end_point.x, seg.end_point.y)
                points.append(corner)
                points.append(end)
                current = end
            else:
                p0 = current
                p1 = (seg.c1.x, seg.c1.y)
                p2 = (seg.c2.x, seg.c2.y)
                p3 = (seg.end_point.x, seg.end_point.y)
                _subdivide_bezier(p0, p1, p2, p3, tolerance, points)
                current = p3

        polylines.append(points)

    return polylines
