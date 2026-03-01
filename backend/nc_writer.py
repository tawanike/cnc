"""NC (G-code) writer: generates plasma-cutter-compatible .nc files.

Output format matches DeskCNC plasma.scpost convention:
- N-numbered lines (increments of 10)
- G21 metric, G40 no cutter comp, G90 absolute
- M08/M09 torch on/off per shape
- G04 dwell for arc stabilization
- G01/G02/G03 for lines and arcs
"""

from dataclasses import dataclass
from datetime import date

from backend.arc_fit import LineSegment, ArcSegment


@dataclass
class CuttingParams:
    """Plasma cutting parameters with sensible defaults."""
    feed_rate: float = 3000.0
    pierce_feed: float = 100.0
    safe_z: float = 10.0
    approach_z: float = 3.0
    cut_z: float = 1.5
    kerf_width: float = 1.5
    dwell: float = 0.5
    filename: str = "output.nc"


Segment = LineSegment | ArcSegment


def write_nc(
    shapes: list[list[Segment]],
    params: CuttingParams | None = None,
) -> bytes:
    """Generate NC (G-code) bytes from a list of shapes.

    Each shape is a list of LineSegment and/or ArcSegment. The writer
    emits rapid moves between shapes and cutting moves within shapes,
    with torch on/off (M08/M09) and pierce dwell per shape.

    Args:
        shapes: List of shapes, each a list of line/arc segments.
        params: Cutting parameters; defaults used if None.

    Returns:
        UTF-8 encoded G-code as bytes.
    """
    if params is None:
        params = CuttingParams()

    lines: list[str] = []
    n = [0]

    def emit(text: str) -> None:
        n[0] += 10
        lines.append(f"N{n[0]:04d} {text}")

    # Header
    emit(f"(Filename: {params.filename})")
    emit(f"(Date: {date.today().strftime('%d/%m/%Y')})")
    emit("G21 (Units: Metric)")
    emit("G40 G90")

    for shape in shapes:
        if not shape:
            continue

        start = shape[0].start

        emit(f"G00 Z{params.safe_z:.4f}")
        emit(f"X{start[0]:.4f} Y{start[1]:.4f}")
        emit(f"Z{params.approach_z:.4f}")
        emit("M08")
        emit(f"G04 P{params.dwell}")
        emit(f"G01 Z{params.cut_z:.4f} F{params.pierce_feed:.0f}")

        for seg in shape:
            if isinstance(seg, LineSegment):
                emit(f"G01 X{seg.end[0]:.4f} Y{seg.end[1]:.4f} F{params.feed_rate:.0f}")
            elif isinstance(seg, ArcSegment):
                code = "G02" if seg.clockwise else "G03"
                i_val = seg.center[0] - seg.start[0]
                j_val = seg.center[1] - seg.start[1]
                emit(
                    f"{code} X{seg.end[0]:.4f} Y{seg.end[1]:.4f} "
                    f"I{i_val:.4f} J{j_val:.4f} F{params.feed_rate:.0f}"
                )

        emit("M09")

    emit(f"G00 Z{params.safe_z:.4f}")
    emit("M09 M30")

    return "\n".join(lines).encode("utf-8")
