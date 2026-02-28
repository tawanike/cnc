"""Potrace tracing wrapper: converts binary bitmaps to Bezier curve paths."""

from dataclasses import dataclass

import numpy as np
from potrace import Bitmap as PotraceBitmap


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


def trace_bitmap(binary_image: np.ndarray) -> list[TracedPath]:
    """Trace a binary image using Potrace and return vector paths.

    Args:
        binary_image: 2D numpy array with 0=black, 255=white.
    Returns:
        List of TracedPath objects containing Bezier curve segments.
    """
    # potracer expects: nonzero = filled. Our convention: 0=black. Invert.
    data = (binary_image < 128).astype(np.uint32)

    # If no filled pixels, return empty list immediately.
    if not data.any():
        return []

    bm = PotraceBitmap(data)
    plist = bm.trace(turdsize=2, alphamax=1.0, opticurve=True, opttolerance=0.2)

    paths: list[TracedPath] = []
    for curve in plist:
        start = Point(x=float(curve.start_point.x), y=float(curve.start_point.y))
        segments: list[BezierSegment] = []
        for segment in curve.segments:
            if segment.is_corner:
                c = Point(x=float(segment.c.x), y=float(segment.c.y))
                end = Point(x=float(segment.end_point.x), y=float(segment.end_point.y))
                segments.append(BezierSegment(c1=c, c2=c, end_point=end, is_corner=True))
            else:
                c1 = Point(x=float(segment.c1.x), y=float(segment.c1.y))
                c2 = Point(x=float(segment.c2.x), y=float(segment.c2.y))
                end = Point(x=float(segment.end_point.x), y=float(segment.end_point.y))
                segments.append(BezierSegment(c1=c1, c2=c2, end_point=end, is_corner=False))
        if segments:
            paths.append(TracedPath(start_point=start, segments=segments))

    return paths
