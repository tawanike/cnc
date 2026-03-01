import io
import ezdxf


def write_dxf(
    polylines: list[list[tuple[float, float]]],
    scale_factor: float = 1.0,
) -> bytes:
    """Write polylines to a DXF file."""
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    for polyline in polylines:
        if len(polyline) < 2:
            continue
        scaled = [(x * scale_factor, y * scale_factor) for x, y in polyline]
        msp.add_lwpolyline(scaled)

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")
