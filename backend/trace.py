"""Bitmap tracing: converts binary images to polyline contours using OpenCV."""

import cv2
import numpy as np
from scipy.interpolate import splprep, splev


def trace_bitmap(
    binary_image: np.ndarray,
    epsilon: float = 0.5,
    min_area: float = 50.0,
    smooth: bool = True,
    spline_points: int = 0,
) -> list[list[tuple[float, float]]]:
    """Trace a binary image and return polyline contours.

    Uses OpenCV findContours with polygon approximation to extract
    vector outlines from a binary bitmap, with optional Gaussian
    pre-smoothing and spline curve fitting.

    Args:
        binary_image: 2D numpy array with 0=black (foreground), 255=white (background).
        epsilon: Approximation accuracy for cv2.approxPolyDP. Smaller values
                 produce more points and closer approximation. Default 0.5px.
        min_area: Minimum contour area in pixels. Contours smaller than this
                  are filtered out as noise. Default 50px.
        smooth: If True, apply Gaussian blur before contour extraction to
                reduce pixel staircase artifacts. Default True.
        spline_points: If > 0, fit a B-spline through each contour and
                       resample at this many points per contour. 0 disables
                       spline fitting. Default 0 (auto: 4x polygon points).

    Returns:
        List of polylines, where each polyline is a list of (x, y) tuples.
    """
    mask = (binary_image < 128).astype(np.uint8) * 255

    if not mask.any():
        return []

    if smooth:
        mask = cv2.GaussianBlur(mask, (5, 5), 1.0)
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    polylines: list[list[tuple[float, float]]] = []
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue

        approx = cv2.approxPolyDP(contour, epsilon, closed=True)
        if len(approx) < 3:
            continue

        points = [(float(pt[0][0]), float(pt[0][1])) for pt in approx]

        if len(points) >= 4:
            points = _fit_spline(points, spline_points)

        # Close the contour
        if points[0] != points[-1]:
            points.append(points[0])

        polylines.append(points)

    return polylines


def _fit_spline(
    points: list[tuple[float, float]],
    num_points: int = 0,
) -> list[tuple[float, float]]:
    """Fit a closed B-spline through polygon points for smooth curves.

    Args:
        points: Input polygon vertices.
        num_points: Number of output points. If 0, uses 4x input count.

    Returns:
        Smoothed points along the spline curve.
    """
    if num_points <= 0:
        num_points = len(points) * 4

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # Close the curve for periodic spline
    xs.append(xs[0])
    ys.append(ys[0])

    try:
        tck, _ = splprep([xs, ys], s=len(points) * 0.5, per=True, k=3)
        u_new = np.linspace(0, 1, num_points)
        x_new, y_new = splev(u_new, tck)
        return [(float(x), float(y)) for x, y in zip(x_new, y_new)]
    except (ValueError, TypeError):
        # Fall back to original points if spline fitting fails
        return points
