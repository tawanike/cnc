"""Bitmap tracing: converts binary images to polyline contours using OpenCV."""

import cv2
import numpy as np


def trace_bitmap(
    binary_image: np.ndarray,
    epsilon: float = 0.5,
    min_points: int = 2,
) -> list[list[tuple[float, float]]]:
    """Trace a binary image and return polyline contours.

    Uses OpenCV findContours with polygon approximation to extract
    vector outlines from a binary bitmap.

    Args:
        binary_image: 2D numpy array with 0=black (foreground), 255=white (background).
        epsilon: Approximation accuracy for cv2.approxPolyDP. Smaller values
                 produce more points and closer approximation. Default 0.5px.
        min_points: Minimum number of points for a contour to be included.

    Returns:
        List of polylines, where each polyline is a list of (x, y) tuples.
    """
    mask = (binary_image < 128).astype(np.uint8) * 255

    if not mask.any():
        return []

    contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    polylines: list[list[tuple[float, float]]] = []
    for contour in contours:
        approx = cv2.approxPolyDP(contour, epsilon, closed=True)
        if len(approx) < min_points:
            continue
        points = [(float(pt[0][0]), float(pt[0][1])) for pt in approx]
        # Close the contour
        if points[0] != points[-1]:
            points.append(points[0])
        polylines.append(points)

    return polylines
