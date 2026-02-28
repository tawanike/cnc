def _fmt(value: float) -> str:
    """Format a number, dropping trailing .0 for clean output."""
    if value == int(value):
        return str(int(value))
    return str(value)


def write_svg(
    polylines: list[list[tuple[float, float]]],
    width: float,
    height: float,
    scale_factor: float = 1.0,
) -> str:
    """Write polylines to an SVG string."""
    sw = _fmt(width * scale_factor)
    sh = _fmt(height * scale_factor)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {sw} {sh}" width="{sw}" height="{sh}">'
    ]
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        points_str = " ".join(
            f"{_fmt(x * scale_factor)},{_fmt(y * scale_factor)}"
            for x, y in polyline
        )
        parts.append(
            f'<polyline points="{points_str}" '
            f'fill="none" stroke="red" stroke-width="1"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)
