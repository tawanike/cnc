import io
import ezdxf
from backend.dxf_writer import write_dxf


def test_write_dxf_returns_bytes():
    """Should return valid DXF file content as bytes."""
    polylines = [
        [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
    ]
    result = write_dxf(polylines)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_write_dxf_contains_polyline():
    """DXF should contain LWPOLYLINE entities."""
    polylines = [
        [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)],
    ]
    result = write_dxf(polylines)
    doc = ezdxf.read(io.StringIO(result.decode("utf-8")))
    msp = doc.modelspace()
    lwpolylines = list(msp.query("LWPOLYLINE"))
    assert len(lwpolylines) == 1


def test_write_dxf_multiple_polylines():
    """Should write multiple polylines as separate entities."""
    polylines = [
        [(0, 0), (50, 0), (50, 50)],
        [(60, 60), (100, 60), (100, 100)],
    ]
    result = write_dxf(polylines)
    doc = ezdxf.read(io.StringIO(result.decode("utf-8")))
    msp = doc.modelspace()
    lwpolylines = list(msp.query("LWPOLYLINE"))
    assert len(lwpolylines) == 2


def test_write_dxf_with_scale():
    """Scaling should multiply all coordinates."""
    polylines = [
        [(0, 0), (10, 0), (10, 10)],
    ]
    result = write_dxf(polylines, scale_factor=2.0)
    doc = ezdxf.read(io.StringIO(result.decode("utf-8")))
    msp = doc.modelspace()
    lwpoly = list(msp.query("LWPOLYLINE"))[0]
    points = list(lwpoly.get_points(format="xy"))
    assert points[1] == (20.0, 0.0)


def test_write_dxf_empty():
    """Empty polylines should produce a valid but empty DXF."""
    result = write_dxf([])
    doc = ezdxf.read(io.StringIO(result.decode("utf-8")))
    msp = doc.modelspace()
    assert len(list(msp.query("LWPOLYLINE"))) == 0
