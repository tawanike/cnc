"""Arc fitting: converts polyline segments to G02/G03 arc and G01 line segments."""

from dataclasses import dataclass
import math


@dataclass
class LineSegment:
    """Straight line from start to end."""
    start: tuple[float, float]
    end: tuple[float, float]


@dataclass
class ArcSegment:
    """Circular arc from start to end around center."""
    start: tuple[float, float]
    end: tuple[float, float]
    center: tuple[float, float]
    clockwise: bool


def fit_arcs(
    points: list[tuple[float, float]],
    tolerance: float = 0.5,
    min_arc_points: int = 3,
) -> list[LineSegment | ArcSegment]:
    """Fit circular arcs and lines to a polyline.

    Walks through points, testing consecutive groups for circular arc fit.
    Uses 3-point circle fitting and extends arcs greedily while points
    remain within tolerance of the fitted circle.

    Args:
        points: Input polyline as (x, y) tuples.
        tolerance: Maximum deviation from arc in mm.
        min_arc_points: Minimum points to consider as an arc.

    Returns:
        List of LineSegment and ArcSegment in order.
    """
    if len(points) < 2:
        return []

    segments: list[LineSegment | ArcSegment] = []
    i = 0

    while i < len(points) - 1:
        arc = _try_fit_arc(points, i, tolerance, min_arc_points)

        if arc is not None:
            seg, consumed = arc
            segments.append(seg)
            i += consumed
        else:
            segments.append(LineSegment(start=points[i], end=points[i + 1]))
            i += 1

    return segments


def _try_fit_arc(
    points: list[tuple[float, float]],
    start_idx: int,
    tolerance: float,
    min_points: int,
) -> tuple[ArcSegment, int] | None:
    """Try to fit an arc starting at start_idx, greedily extending."""
    if start_idx + min_points > len(points):
        return None

    p0 = points[start_idx]
    p1 = points[start_idx + min_points // 2]
    p2 = points[start_idx + min_points - 1]

    center = _circle_center(p0, p1, p2)
    if center is None:
        return None

    radius = math.dist(center, p0)
    if radius < 1e-6 or radius > 1e6:
        return None

    end_idx = start_idx + min_points - 1
    for j in range(start_idx + min_points, len(points)):
        d = abs(math.dist(center, points[j]) - radius)
        if d > tolerance:
            break
        end_idx = j

    consumed = end_idx - start_idx
    if consumed < min_points - 1:
        return None

    # Verify midpoints of consecutive chords also lie on the circle.
    # This rejects polygons (e.g. squares) whose vertices happen to
    # sit on a circle but whose edges are straight, not curved.
    for k in range(start_idx, end_idx):
        mx = (points[k][0] + points[k + 1][0]) / 2
        my = (points[k][1] + points[k + 1][1]) / 2
        d = abs(math.dist((mx, my), center) - radius)
        if d > tolerance:
            return None

    clockwise = _is_clockwise(points[start_idx], points[start_idx + 1], center)

    arc = ArcSegment(
        start=points[start_idx],
        end=points[end_idx],
        center=center,
        clockwise=clockwise,
    )
    return arc, consumed


def _circle_center(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> tuple[float, float] | None:
    """Find center of circle through 3 points. Returns None if collinear."""
    ax, ay = p1
    bx, by = p2
    cx, cy = p3

    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-10:
        return None

    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy)


def _is_clockwise(
    start: tuple[float, float],
    next_pt: tuple[float, float],
    center: tuple[float, float],
) -> bool:
    """Determine if arc from start through next_pt is clockwise around center."""
    dx1 = start[0] - center[0]
    dy1 = start[1] - center[1]
    dx2 = next_pt[0] - center[0]
    dy2 = next_pt[1] - center[1]
    cross = dx1 * dy2 - dy1 * dx2
    return cross < 0
