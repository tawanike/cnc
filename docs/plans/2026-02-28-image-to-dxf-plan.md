# Image-to-DXF Converter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web app that converts PNG/JPEG images to DXF files using OpenCV preprocessing and Potrace vectorization.

**Architecture:** React frontend (Vite + TypeScript) talks to a FastAPI backend. The backend runs a processing pipeline: classify image type → preprocess → trace with Potrace → flatten Bezier curves to polylines → write DXF with ezdxf. The frontend provides drag-and-drop upload, scale input, SVG preview, and DXF download.

**Tech Stack:** Python 3.12, FastAPI, OpenCV, potracer (pure Python Potrace), ezdxf, React, Vite, TypeScript

---

### Task 1: Project scaffolding and dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/.gitkeep`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend tests/fixtures
touch backend/__init__.py tests/__init__.py tests/fixtures/.gitkeep
```

**Step 2: Create requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
opencv-python-headless==4.10.0.84
numpy>=1.26.0
potracer==0.0.4
ezdxf==1.4.2
Pillow>=10.0.0
pytest==8.3.4
httpx==0.28.1
```

Write this to `backend/requirements.txt`.

**Step 3: Install dependencies**

Run: `pip install -r backend/requirements.txt`
Expected: all packages install successfully

**Step 4: Create a test image fixture**

Create a simple 100x100 black-and-white test PNG programmatically:

```python
# tests/create_fixtures.py
import numpy as np
from PIL import Image

# Line art: black rectangle on white background
img = np.ones((100, 100), dtype=np.uint8) * 255
img[20:80, 20:80] = 0  # black square
Image.fromarray(img).save("tests/fixtures/square_lineart.png")

# Photo-like: gradient with noise
rng = np.random.default_rng(42)
img2 = np.zeros((100, 100), dtype=np.uint8)
img2[25:75, 25:75] = 180
img2 = img2 + rng.integers(0, 30, size=(100, 100), dtype=np.uint8)
Image.fromarray(img2).save("tests/fixtures/noisy_photo.png")
```

Run: `python tests/create_fixtures.py`
Expected: Two PNG files created in `tests/fixtures/`

**Step 5: Commit**

```bash
git add backend/ tests/
git commit -m "feat: project scaffolding and dependencies"
```

---

### Task 2: Image classifier — line art vs photo detection

**Files:**
- Create: `backend/classify.py`
- Create: `tests/test_classify.py`

**Step 1: Write the failing test**

```python
# tests/test_classify.py
import numpy as np
from backend.classify import classify_image, ImageType


def test_classify_lineart():
    """A bimodal image (mostly black and white) should be classified as line art."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    assert classify_image(img) == ImageType.LINE_ART


def test_classify_photo():
    """An image with spread intensity distribution should be classified as photo."""
    rng = np.random.default_rng(42)
    img = rng.integers(50, 200, size=(100, 100), dtype=np.uint8)
    assert classify_image(img) == ImageType.PHOTO


def test_classify_already_grayscale():
    """Should handle both grayscale and color input."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    assert classify_image(img) == ImageType.LINE_ART
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_classify.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'backend.classify'`

**Step 3: Write minimal implementation**

```python
# backend/classify.py
from enum import Enum

import cv2
import numpy as np


class ImageType(Enum):
    LINE_ART = "line_art"
    PHOTO = "photo"


def classify_image(img: np.ndarray) -> ImageType:
    """Classify an image as line art or photo based on intensity distribution.

    Line art has a bimodal distribution (mostly black and white pixels).
    Photos have a spread distribution across the intensity range.
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    total_pixels = gray.size
    near_black = np.sum(gray < 51)   # within 20% of 0
    near_white = np.sum(gray > 204)  # within 20% of 255
    extreme_ratio = (near_black + near_white) / total_pixels

    if extreme_ratio > 0.7:
        return ImageType.LINE_ART
    return ImageType.PHOTO
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_classify.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/classify.py tests/test_classify.py
git commit -m "feat: image classifier for line art vs photo detection"
```

---

### Task 3: Image preprocessing

**Files:**
- Create: `backend/preprocess.py`
- Create: `tests/test_preprocess.py`

**Step 1: Write the failing test**

```python
# tests/test_preprocess.py
import numpy as np
from backend.classify import ImageType
from backend.preprocess import preprocess_image


def test_preprocess_lineart_returns_binary():
    """Line art preprocessing should return a binary image (only 0 and 255)."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    result = preprocess_image(img, ImageType.LINE_ART)
    unique_values = set(np.unique(result))
    assert unique_values.issubset({0, 255})


def test_preprocess_photo_returns_binary():
    """Photo preprocessing should return a binary image."""
    rng = np.random.default_rng(42)
    img = np.zeros((100, 100), dtype=np.uint8)
    img[25:75, 25:75] = 180
    img = img + rng.integers(0, 30, size=(100, 100), dtype=np.uint8)
    result = preprocess_image(img, ImageType.PHOTO)
    unique_values = set(np.unique(result))
    assert unique_values.issubset({0, 255})


def test_preprocess_output_shape():
    """Output should be 2D regardless of input."""
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    result = preprocess_image(img, ImageType.LINE_ART)
    assert len(result.shape) == 2


def test_preprocess_preserves_content():
    """Preprocessing should not destroy the main shape."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[30:70, 30:70] = 0  # black square in center
    result = preprocess_image(img, ImageType.LINE_ART)
    # Center should still be black (0)
    assert result[50, 50] == 0
    # Corner should still be white (255)
    assert result[5, 5] == 255
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_preprocess.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# backend/preprocess.py
import cv2
import numpy as np

from backend.classify import ImageType


def preprocess_image(img: np.ndarray, image_type: ImageType) -> np.ndarray:
    """Preprocess image to binary bitmap based on image type.

    Returns a binary image with values 0 (black) and 255 (white).
    """
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()

    if image_type == ImageType.LINE_ART:
        return _preprocess_lineart(gray)
    return _preprocess_photo(gray)


def _preprocess_lineart(gray: np.ndarray) -> np.ndarray:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return binary


def _preprocess_photo(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (5, 5), 2)
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return binary
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_preprocess.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/preprocess.py tests/test_preprocess.py
git commit -m "feat: image preprocessing for line art and photos"
```

---

### Task 4: Potrace tracing wrapper

**Files:**
- Create: `backend/trace.py`
- Create: `tests/test_trace.py`

**Step 1: Write the failing test**

```python
# tests/test_trace.py
import numpy as np
from backend.trace import trace_bitmap, TracedPath


def test_trace_returns_paths():
    """Tracing a simple shape should return at least one path."""
    # White background, black square
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    paths = trace_bitmap(bitmap)
    assert len(paths) > 0


def test_traced_path_has_segments():
    """Each path should have a start point and segments."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    bitmap[20:80, 20:80] = 0
    paths = trace_bitmap(bitmap)
    for path in paths:
        assert path.start_point is not None
        assert len(path.segments) > 0


def test_trace_empty_image_returns_no_paths():
    """An all-white image should return no paths."""
    bitmap = np.ones((100, 100), dtype=np.uint8) * 255
    paths = trace_bitmap(bitmap)
    assert len(paths) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_trace.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# backend/trace.py
from dataclasses import dataclass
from typing import Optional

import numpy as np
from potrace import Bitmap as PotraceBitmap


@dataclass
class Point:
    x: float
    y: float


@dataclass
class BezierSegment:
    """A cubic Bezier curve segment."""
    c1: Point  # control point 1
    c2: Point  # control point 2
    end_point: Point
    is_corner: bool


@dataclass
class TracedPath:
    start_point: Point
    segments: list[BezierSegment]


def trace_bitmap(binary_image: np.ndarray) -> list[TracedPath]:
    """Trace a binary image using Potrace and return vector paths.

    Args:
        binary_image: 2D numpy array with 0=black, 255=white.
                      Potrace traces boundaries of black regions.

    Returns:
        List of TracedPath objects containing Bezier curve segments.
    """
    # potracer expects: nonzero = filled (black in our case)
    # Our convention: 0=black, 255=white. Invert so black pixels are nonzero.
    data = (binary_image < 128).astype(np.uint32)

    bm = PotraceBitmap(data)
    plist = bm.trace(turdsize=2, alphamax=1.0, opticurve=True, opttolerance=0.2)

    paths: list[TracedPath] = []
    for curve in plist:
        start = Point(x=float(curve.start_point.x), y=float(curve.start_point.y))
        segments: list[BezierSegment] = []
        for segment in curve.segments:
            if segment.is_corner:
                # Corner: line to c, then line to end_point
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_trace.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add backend/trace.py tests/test_trace.py
git commit -m "feat: Potrace tracing wrapper"
```

---

### Task 5: Bezier to polyline conversion

**Files:**
- Create: `backend/bezier.py`
- Create: `tests/test_bezier.py`

**Step 1: Write the failing test**

```python
# tests/test_bezier.py
import math
from backend.trace import Point, BezierSegment, TracedPath
from backend.bezier import flatten_paths


def test_flatten_straight_line():
    """A 'bezier' that is actually a straight line should produce minimal points."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(33, 0), c2=Point(66, 0), end_point=Point(100, 0),
                is_corner=False,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    # Start and end should match
    assert polylines[0][0] == (0.0, 0.0)
    assert polylines[0][-1] == (100.0, 0.0)


def test_flatten_curve_produces_multiple_points():
    """A real curve should produce multiple intermediate points."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(0, 100), c2=Point(100, 100), end_point=Point(100, 0),
                is_corner=False,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    assert len(polylines[0]) > 2  # Should have intermediate points


def test_flatten_corner_segment():
    """A corner segment should produce line segments."""
    path = TracedPath(
        start_point=Point(0, 0),
        segments=[
            BezierSegment(
                c1=Point(50, 0), c2=Point(50, 0), end_point=Point(50, 50),
                is_corner=True,
            )
        ],
    )
    polylines = flatten_paths([path], tolerance=0.1)
    assert len(polylines) == 1
    assert (0.0, 0.0) in polylines[0]
    assert (50.0, 0.0) in polylines[0]
    assert (50.0, 50.0) in polylines[0]


def test_flatten_empty():
    """Empty input should return empty output."""
    assert flatten_paths([], tolerance=0.1) == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bezier.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# backend/bezier.py
from backend.trace import Point, BezierSegment, TracedPath


def _subdivide_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    tolerance: float,
    points: list[tuple[float, float]],
) -> None:
    """Recursively subdivide a cubic Bezier curve into line segments."""
    # Flatness test: check if control points are close to the line p0-p3
    dx = p3[0] - p0[0]
    dy = p3[1] - p0[1]
    d2 = abs((p1[0] - p3[0]) * dy - (p1[1] - p3[1]) * dx)
    d3 = abs((p2[0] - p3[0]) * dy - (p2[1] - p3[1]) * dx)

    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        points.append(p3)
        return

    if (d2 + d3) ** 2 <= tolerance * tolerance * length_sq:
        points.append(p3)
        return

    # Subdivide at midpoint using De Casteljau's algorithm
    m01 = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    m12 = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    m23 = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
    m012 = ((m01[0] + m12[0]) / 2, (m01[1] + m12[1]) / 2)
    m123 = ((m12[0] + m23[0]) / 2, (m12[1] + m23[1]) / 2)
    mid = ((m012[0] + m123[0]) / 2, (m012[1] + m123[1]) / 2)

    _subdivide_bezier(p0, m01, m012, mid, tolerance, points)
    _subdivide_bezier(mid, m123, m23, p3, tolerance, points)


def flatten_paths(
    paths: list[TracedPath], tolerance: float = 0.1
) -> list[list[tuple[float, float]]]:
    """Convert Bezier curve paths to polylines.

    Args:
        paths: List of TracedPath objects from Potrace.
        tolerance: Maximum deviation from true curve in output units.

    Returns:
        List of polylines, where each polyline is a list of (x, y) tuples.
    """
    polylines: list[list[tuple[float, float]]] = []

    for path in paths:
        points: list[tuple[float, float]] = [(path.start_point.x, path.start_point.y)]
        current = (path.start_point.x, path.start_point.y)

        for seg in path.segments:
            if seg.is_corner:
                corner = (seg.c1.x, seg.c1.y)
                end = (seg.end_point.x, seg.end_point.y)
                points.append(corner)
                points.append(end)
                current = end
            else:
                p0 = current
                p1 = (seg.c1.x, seg.c1.y)
                p2 = (seg.c2.x, seg.c2.y)
                p3 = (seg.end_point.x, seg.end_point.y)
                _subdivide_bezier(p0, p1, p2, p3, tolerance, points)
                current = p3

        polylines.append(points)

    return polylines
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bezier.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/bezier.py tests/test_bezier.py
git commit -m "feat: Bezier curve to polyline flattening"
```

---

### Task 6: DXF writer

**Files:**
- Create: `backend/dxf_writer.py`
- Create: `tests/test_dxf_writer.py`

**Step 1: Write the failing test**

```python
# tests/test_dxf_writer.py
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
    doc = ezdxf.read(io.BytesIO(result))
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
    doc = ezdxf.read(io.BytesIO(result))
    msp = doc.modelspace()
    lwpolylines = list(msp.query("LWPOLYLINE"))
    assert len(lwpolylines) == 2


def test_write_dxf_with_scale():
    """Scaling should multiply all coordinates."""
    polylines = [
        [(0, 0), (10, 0), (10, 10)],
    ]
    result = write_dxf(polylines, scale_factor=2.0)
    doc = ezdxf.read(io.BytesIO(result))
    msp = doc.modelspace()
    lwpoly = list(msp.query("LWPOLYLINE"))[0]
    points = list(lwpoly.get_points(format="xy"))
    assert points[1] == (20.0, 0.0)


def test_write_dxf_empty():
    """Empty polylines should produce a valid but empty DXF."""
    result = write_dxf([])
    doc = ezdxf.read(io.BytesIO(result))
    msp = doc.modelspace()
    assert len(list(msp.query("LWPOLYLINE"))) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dxf_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# backend/dxf_writer.py
import io
import ezdxf


def write_dxf(
    polylines: list[list[tuple[float, float]]],
    scale_factor: float = 1.0,
) -> bytes:
    """Write polylines to a DXF file.

    Args:
        polylines: List of polylines, each a list of (x, y) tuples.
        scale_factor: Multiply all coordinates by this value.

    Returns:
        DXF file content as bytes.
    """
    doc = ezdxf.new(dxfversion="R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()

    for polyline in polylines:
        if len(polyline) < 2:
            continue
        scaled = [(x * scale_factor, y * scale_factor) for x, y in polyline]
        msp.add_lwpolyline(scaled)

    buffer = io.BytesIO()
    doc.write(buffer)
    return buffer.getvalue()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dxf_writer.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add backend/dxf_writer.py tests/test_dxf_writer.py
git commit -m "feat: DXF writer with scaling support"
```

---

### Task 7: Processing pipeline — ties everything together

**Files:**
- Create: `backend/pipeline.py`
- Create: `tests/test_pipeline.py`

**Step 1: Write the failing test**

```python
# tests/test_pipeline.py
import io
import numpy as np
import ezdxf
from PIL import Image
from backend.pipeline import convert_image_to_dxf, ConversionResult


def _make_test_image() -> bytes:
    """Create a simple test PNG as bytes."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def test_convert_returns_result():
    """Pipeline should return a ConversionResult with DXF bytes."""
    image_bytes = _make_test_image()
    result = convert_image_to_dxf(image_bytes)
    assert isinstance(result, ConversionResult)
    assert isinstance(result.dxf_bytes, bytes)
    assert len(result.dxf_bytes) > 0


def test_convert_produces_valid_dxf():
    """Output should be parseable as DXF."""
    image_bytes = _make_test_image()
    result = convert_image_to_dxf(image_bytes)
    doc = ezdxf.read(io.BytesIO(result.dxf_bytes))
    msp = doc.modelspace()
    polylines = list(msp.query("LWPOLYLINE"))
    assert len(polylines) > 0


def test_convert_with_target_width():
    """Specifying target width should scale the output."""
    image_bytes = _make_test_image()
    result = convert_image_to_dxf(image_bytes, target_width_mm=200.0)
    assert result.scale_factor == 2.0  # 200mm / 100px


def test_convert_returns_stats():
    """Result should include path and point count stats."""
    image_bytes = _make_test_image()
    result = convert_image_to_dxf(image_bytes)
    assert result.path_count > 0
    assert result.point_count > 0
    assert result.width_mm > 0
    assert result.height_mm > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# backend/pipeline.py
from dataclasses import dataclass

import cv2
import numpy as np

from backend.classify import classify_image
from backend.preprocess import preprocess_image
from backend.trace import trace_bitmap
from backend.bezier import flatten_paths
from backend.dxf_writer import write_dxf


@dataclass
class ConversionResult:
    dxf_bytes: bytes
    svg_paths: str
    path_count: int
    point_count: int
    width_mm: float
    height_mm: float
    scale_factor: float
    image_type: str


def convert_image_to_dxf(
    image_bytes: bytes,
    target_width_mm: float | None = None,
    target_height_mm: float | None = None,
    tolerance: float = 0.1,
) -> ConversionResult:
    """Full pipeline: image bytes → DXF bytes.

    Args:
        image_bytes: Raw PNG/JPEG file content.
        target_width_mm: Desired output width in mm. Mutually exclusive with target_height_mm.
        target_height_mm: Desired output height in mm. Mutually exclusive with target_width_mm.
        tolerance: Bezier flattening tolerance in mm.

    Returns:
        ConversionResult with DXF bytes and metadata.
    """
    # Decode image
    img_array = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    height_px, width_px = img.shape[:2]

    # Classify
    image_type = classify_image(img)

    # Preprocess
    binary = preprocess_image(img, image_type)

    # Trace
    paths = trace_bitmap(binary)

    # Flatten Bezier curves to polylines
    polylines = flatten_paths(paths, tolerance=tolerance)

    # Calculate scale factor (default: 1px = 1mm)
    scale_factor = 1.0
    if target_width_mm is not None:
        scale_factor = target_width_mm / width_px
    elif target_height_mm is not None:
        scale_factor = target_height_mm / height_px

    # Flip Y axis (image Y goes down, DXF Y goes up)
    flipped: list[list[tuple[float, float]]] = []
    for polyline in polylines:
        flipped.append([(x, height_px - y) for x, y in polyline])

    # Write DXF
    dxf_bytes = write_dxf(flipped, scale_factor=scale_factor)

    # Generate SVG preview
    svg_paths = _generate_svg(flipped, width_px, height_px, scale_factor)

    # Stats
    total_points = sum(len(pl) for pl in flipped)

    return ConversionResult(
        dxf_bytes=dxf_bytes,
        svg_paths=svg_paths,
        path_count=len(flipped),
        point_count=total_points,
        width_mm=width_px * scale_factor,
        height_mm=height_px * scale_factor,
        scale_factor=scale_factor,
        image_type=image_type.value,
    )


def _generate_svg(
    polylines: list[list[tuple[float, float]]],
    width_px: int,
    height_px: int,
    scale_factor: float,
) -> str:
    """Generate an SVG string from polylines for preview."""
    w = width_px * scale_factor
    h = height_px * scale_factor
    paths = []
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        d = f"M {polyline[0][0] * scale_factor},{polyline[0][1] * scale_factor}"
        for x, y in polyline[1:]:
            d += f" L {x * scale_factor},{y * scale_factor}"
        d += " Z"
        paths.append(f'<path d="{d}" fill="none" stroke="black" stroke-width="0.5"/>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"'
        f' width="{w}" height="{h}">'
        + "".join(paths)
        + "</svg>"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipeline.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/pipeline.py tests/test_pipeline.py
git commit -m "feat: full image-to-DXF processing pipeline"
```

---

### Task 8: FastAPI backend

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

```python
# tests/test_api.py
import io
import numpy as np
from PIL import Image
from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

from backend.main import app


def _make_png_bytes() -> bytes:
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def png_bytes():
    return _make_png_bytes()


@pytest.mark.asyncio
async def test_convert_endpoint(png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png_bytes, "image/png")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_preview_endpoint(png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/preview",
            files={"image": ("test.png", png_bytes, "image/png")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert "stats" in data
    assert data["stats"]["path_count"] > 0


@pytest.mark.asyncio
async def test_convert_with_scale(png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png_bytes, "image/png")},
            data={"target_width_mm": "200"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_convert_invalid_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("test.txt", b"not an image", "text/plain")},
        )
    assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

Note: Add `pytest-asyncio` to requirements.txt:

```
pytest-asyncio==0.24.0
```

Run: `pip install pytest-asyncio==0.24.0`

**Step 3: Write minimal implementation**

```python
# backend/main.py
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional

from backend.pipeline import convert_image_to_dxf

app = FastAPI(title="Image to DXF Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/convert")
async def convert(
    image: UploadFile = File(...),
    target_width_mm: Optional[float] = Form(None),
    target_height_mm: Optional[float] = Form(None),
):
    image_bytes = await image.read()
    try:
        result = convert_image_to_dxf(
            image_bytes,
            target_width_mm=target_width_mm,
            target_height_mm=target_height_mm,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(
        content=result.dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": "attachment; filename=output.dxf"},
    )


@app.post("/api/preview")
async def preview(
    image: UploadFile = File(...),
    target_width_mm: Optional[float] = Form(None),
    target_height_mm: Optional[float] = Form(None),
):
    image_bytes = await image.read()
    try:
        result = convert_image_to_dxf(
            image_bytes,
            target_width_mm=target_width_mm,
            target_height_mm=target_height_mm,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "svg": result.svg_paths,
        "stats": {
            "path_count": result.path_count,
            "point_count": result.point_count,
            "width_mm": result.width_mm,
            "height_mm": result.height_mm,
            "image_type": result.image_type,
        },
    }


# Mount frontend static files (only if the build directory exists)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add backend/main.py tests/test_api.py backend/requirements.txt
git commit -m "feat: FastAPI backend with convert and preview endpoints"
```

---

### Task 9: React frontend — project setup

**Files:**
- Create: `frontend/` (via Vite scaffold)
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Scaffold React project**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

**Step 2: Configure Vite proxy to backend**

Replace `frontend/vite.config.ts` with:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

**Step 3: Clean up default Vite files**

- Delete `frontend/src/App.css` contents (will replace)
- Delete `frontend/src/assets/` directory
- Clear `frontend/src/index.css` (will replace)

**Step 4: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with Vite"
```

---

### Task 10: React frontend — DropZone component

**Files:**
- Create: `frontend/src/components/DropZone.tsx`

**Step 1: Write DropZone component**

```tsx
// frontend/src/components/DropZone.tsx
import { useCallback, useState, DragEvent, ChangeEvent } from "react";

interface DropZoneProps {
  onFileSelected: (file: File) => void;
  disabled?: boolean;
}

export function DropZone({ onFileSelected, disabled }: DropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file && (file.type === "image/png" || file.type === "image/jpeg")) {
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelected(file);
      }
    },
    [onFileSelected]
  );

  return (
    <div
      className={`dropzone ${isDragOver ? "dropzone--active" : ""} ${disabled ? "dropzone--disabled" : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <p>Drag & drop a PNG or JPEG image here</p>
      <p>or</p>
      <label className="dropzone__button">
        Choose File
        <input
          type="file"
          accept="image/png,image/jpeg"
          onChange={handleFileInput}
          disabled={disabled}
          hidden
        />
      </label>
    </div>
  );
}
```

**Step 2: Commit**

```bash
git add frontend/src/components/DropZone.tsx
git commit -m "feat: DropZone drag-and-drop component"
```

---

### Task 11: React frontend — ScaleInput and Preview components

**Files:**
- Create: `frontend/src/components/ScaleInput.tsx`
- Create: `frontend/src/components/Preview.tsx`

**Step 1: Write ScaleInput component**

```tsx
// frontend/src/components/ScaleInput.tsx
interface ScaleInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ScaleInput({ value, onChange, disabled }: ScaleInputProps) {
  return (
    <div className="scale-input">
      <label htmlFor="target-width">Target width (mm):</label>
      <input
        id="target-width"
        type="number"
        min="1"
        step="1"
        placeholder="Leave empty for 1px = 1mm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
    </div>
  );
}
```

**Step 2: Write Preview component**

```tsx
// frontend/src/components/Preview.tsx
interface PreviewProps {
  svgContent: string;
  originalImageUrl: string;
  stats: {
    path_count: number;
    point_count: number;
    width_mm: number;
    height_mm: number;
    image_type: string;
  };
}

export function Preview({ svgContent, originalImageUrl, stats }: PreviewProps) {
  return (
    <div className="preview">
      <div className="preview__images">
        <div className="preview__panel">
          <h3>Original</h3>
          <img src={originalImageUrl} alt="Original" />
        </div>
        <div className="preview__panel">
          <h3>Traced</h3>
          <div dangerouslySetInnerHTML={{ __html: svgContent }} />
        </div>
      </div>
      <div className="preview__stats">
        <span>Type: {stats.image_type}</span>
        <span>Paths: {stats.path_count}</span>
        <span>Points: {stats.point_count}</span>
        <span>
          Size: {stats.width_mm.toFixed(1)} x {stats.height_mm.toFixed(1)} mm
        </span>
      </div>
    </div>
  );
}
```

**Step 3: Commit**

```bash
git add frontend/src/components/ScaleInput.tsx frontend/src/components/Preview.tsx
git commit -m "feat: ScaleInput and Preview components"
```

---

### Task 12: React frontend — App component and styling

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/index.css`

**Step 1: Write App.tsx**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";
import { Preview } from "./components/Preview";

type Status = "idle" | "processing" | "done" | "error";

interface PreviewData {
  svg: string;
  stats: {
    path_count: number;
    point_count: number;
    width_mm: number;
    height_mm: number;
    image_type: string;
  };
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetWidth, setTargetWidth] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [imageUrl, setImageUrl] = useState("");

  const handleFileSelected = async (selectedFile: File) => {
    setFile(selectedFile);
    setImageUrl(URL.createObjectURL(selectedFile));
    setStatus("processing");
    setError("");
    setPreview(null);

    const formData = new FormData();
    formData.append("image", selectedFile);
    if (targetWidth) {
      formData.append("target_width_mm", targetWidth);
    }

    try {
      const response = await fetch("/api/preview", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Conversion failed");
      }
      const data: PreviewData = await response.json();
      setPreview(data);
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setStatus("error");
    }
  };

  const handleDownload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);
    if (targetWidth) {
      formData.append("target_width_mm", targetWidth);
    }

    try {
      const response = await fetch("/api/convert", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) throw new Error("Download failed");

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(/\.(png|jpe?g)$/i, ".dxf");
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setStatus("idle");
    setError("");
    setImageUrl("");
  };

  return (
    <div className="app">
      <header className="app__header">
        <h1>Image to DXF Converter</h1>
        <p>Upload a PNG or JPEG image to convert it to a DXF file for CNC</p>
      </header>

      <main className="app__main">
        <ScaleInput
          value={targetWidth}
          onChange={setTargetWidth}
          disabled={status === "processing"}
        />

        {status === "idle" && (
          <DropZone onFileSelected={handleFileSelected} />
        )}

        {status === "processing" && (
          <div className="loading">
            <div className="spinner" />
            <p>Tracing image...</p>
          </div>
        )}

        {status === "error" && (
          <div className="error">
            <p>{error}</p>
            <button onClick={handleReset}>Try again</button>
          </div>
        )}

        {status === "done" && preview && (
          <>
            <Preview
              svgContent={preview.svg}
              originalImageUrl={imageUrl}
              stats={preview.stats}
            />
            <div className="actions">
              <button className="button--primary" onClick={handleDownload}>
                Download DXF
              </button>
              <button onClick={handleReset}>Convert another</button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
```

**Step 2: Write index.css**

```css
/* frontend/src/index.css */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f5f5f5;
  color: #222;
  min-height: 100vh;
}

.app {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.app__header {
  text-align: center;
  margin-bottom: 2rem;
}

.app__header h1 {
  font-size: 1.8rem;
  margin-bottom: 0.5rem;
}

.app__header p {
  color: #666;
}

.app__main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* DropZone */
.dropzone {
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.dropzone--active {
  border-color: #2563eb;
  background: #eff6ff;
}

.dropzone--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropzone p {
  margin: 0.5rem 0;
  color: #666;
}

.dropzone__button {
  display: inline-block;
  padding: 0.6rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  margin-top: 0.5rem;
}

.dropzone__button:hover {
  background: #1d4ed8;
}

/* Scale Input */
.scale-input {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.scale-input label {
  font-weight: 500;
  white-space: nowrap;
}

.scale-input input {
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.95rem;
  width: 200px;
}

/* Preview */
.preview__images {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.preview__panel {
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.preview__panel h3 {
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preview__panel img,
.preview__panel svg {
  max-width: 100%;
  height: auto;
}

.preview__stats {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  padding: 0.75rem;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e5e5;
  font-size: 0.85rem;
  color: #666;
}

/* Loading */
.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e5e5;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.error {
  text-align: center;
  padding: 2rem;
  color: #dc2626;
}

.error button {
  margin-top: 1rem;
}

/* Actions */
.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

button {
  padding: 0.6rem 1.5rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 0.95rem;
}

button:hover {
  background: #f5f5f5;
}

.button--primary {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
}

.button--primary:hover {
  background: #1d4ed8;
}
```

**Step 3: Verify frontend builds**

```bash
cd frontend && npm run build
```

Expected: Build succeeds, `frontend/dist/` created

**Step 4: Commit**

```bash
git add frontend/src/App.tsx frontend/src/index.css
git commit -m "feat: main App component with upload, preview, and download flow"
```

---

### Task 13: Integration test — full end-to-end

**Files:**
- Create: `tests/test_e2e.py`

**Step 1: Write end-to-end test**

```python
# tests/test_e2e.py
"""End-to-end test: upload image → get DXF → verify DXF has geometry."""
import io
import numpy as np
import ezdxf
from PIL import Image
from httpx import AsyncClient, ASGITransport
import pytest

from backend.main import app


def _make_circle_png() -> bytes:
    """Create a PNG with a filled circle — more realistic test than a square."""
    img = np.ones((200, 200), dtype=np.uint8) * 255
    cy, cx = 100, 100
    for y in range(200):
        for x in range(200):
            if (x - cx) ** 2 + (y - cy) ** 2 < 60**2:
                img[y, x] = 0
    pil_img = Image.fromarray(img)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_full_round_trip():
    """Upload a circle image, get DXF, verify it contains a closed polyline."""
    png_bytes = _make_circle_png()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get preview
        preview_resp = await client.post(
            "/api/preview",
            files={"image": ("circle.png", png_bytes, "image/png")},
            data={"target_width_mm": "100"},
        )
        assert preview_resp.status_code == 200
        stats = preview_resp.json()["stats"]
        assert stats["path_count"] >= 1
        assert stats["width_mm"] == 100.0

        # Get DXF
        dxf_resp = await client.post(
            "/api/convert",
            files={"image": ("circle.png", png_bytes, "image/png")},
            data={"target_width_mm": "100"},
        )
        assert dxf_resp.status_code == 200

    # Parse the DXF and verify geometry
    doc = ezdxf.read(io.BytesIO(dxf_resp.content))
    msp = doc.modelspace()
    polylines = list(msp.query("LWPOLYLINE"))
    assert len(polylines) >= 1

    # Verify the polyline has reasonable number of points (circle should have many)
    points = list(polylines[0].get_points(format="xy"))
    assert len(points) > 10
```

**Step 2: Run test**

Run: `pytest tests/test_e2e.py -v`
Expected: 1 passed

**Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/test_e2e.py
git commit -m "test: end-to-end round-trip test"
```

---

### Task 14: Run script and .gitignore

**Files:**
- Create: `run.sh`
- Create: `.gitignore`

**Step 1: Create run script**

```bash
#!/usr/bin/env bash
# run.sh — Start both backend and frontend dev servers
set -e

echo "Starting backend on :8000..."
cd "$(dirname "$0")"
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting frontend on :3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
wait
```

```bash
chmod +x run.sh
```

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
node_modules/
frontend/dist/
.env
venv/
```

**Step 3: Commit**

```bash
git add run.sh .gitignore
git commit -m "chore: add run script and gitignore"
```

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Project scaffolding & dependencies | - |
| 2 | Image classifier (line art vs photo) | 3 |
| 3 | Image preprocessing | 4 |
| 4 | Potrace tracing wrapper | 3 |
| 5 | Bezier to polyline conversion | 4 |
| 6 | DXF writer | 5 |
| 7 | Processing pipeline | 4 |
| 8 | FastAPI backend | 4 |
| 9 | React frontend setup | - |
| 10 | DropZone component | - |
| 11 | ScaleInput + Preview components | - |
| 12 | App component + styling | - |
| 13 | End-to-end integration test | 1 |
| 14 | Run script + gitignore | - |

**Total: 14 tasks, 28 tests**
