"""Data classes for Potrace-style Bezier curve tracing output."""

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
