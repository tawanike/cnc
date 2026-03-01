"""Kerf compensation: offsets closed polyline contours outward."""

import pyclipper


# Clipper uses integer coordinates; scale floats to preserve precision
_CLIPPER_SCALE = 1000


def offset_polylines(
    polylines: list[list[tuple[float, float]]],
    kerf_width: float,
) -> list[list[tuple[float, float]]]:
    """Offset closed polyline contours outward by half the kerf width.

    Args:
        polylines: Closed polylines (first point == last point).
        kerf_width: Full kerf width in mm. Offset = kerf_width / 2.

    Returns:
        Offset polylines in the same format, closed.
    """
    if not polylines or kerf_width == 0.0:
        return polylines

    offset_distance = kerf_width / 2.0

    result: list[list[tuple[float, float]]] = []
    pco = pyclipper.PyclipperOffset()

    for poly in polylines:
        pco.Clear()
        # Remove closing point for Clipper (it auto-closes)
        points = poly[:-1] if poly[0] == poly[-1] else poly
        scaled = [(int(x * _CLIPPER_SCALE), int(y * _CLIPPER_SCALE)) for x, y in points]

        pco.AddPath(scaled, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        expanded = pco.Execute(offset_distance * _CLIPPER_SCALE)

        for path in expanded:
            contour = [(x / _CLIPPER_SCALE, y / _CLIPPER_SCALE) for x, y in path]
            contour.append(contour[0])  # close
            result.append(contour)

    return result
