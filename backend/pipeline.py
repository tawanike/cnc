import cv2
import numpy as np

from backend.classify import classify_image
from backend.preprocess import preprocess_image
from backend.trace import trace_bitmap
from backend.bezier import flatten_paths
from backend.dxf_writer import write_dxf
from backend.svg_writer import write_svg


def _decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes to numpy array."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img


def _compute_scale(
    img_width: int,
    img_height: int,
    target_width_mm: float | None,
    target_height_mm: float | None,
) -> float:
    """Compute scale factor from optional target dimensions."""
    if target_width_mm is not None:
        return target_width_mm / img_width
    if target_height_mm is not None:
        return target_height_mm / img_height
    return 1.0


def convert_image(
    image_bytes: bytes,
    filename: str,
    target_width_mm: float | None = None,
    target_height_mm: float | None = None,
) -> bytes:
    """Full pipeline: image bytes to DXF bytes."""
    img = _decode_image(image_bytes)
    image_type = classify_image(img)
    binary = preprocess_image(img, image_type)
    paths = trace_bitmap(binary)
    polylines = flatten_paths(paths)
    scale = _compute_scale(img.shape[1], img.shape[0], target_width_mm, target_height_mm)
    return write_dxf(polylines, scale_factor=scale)


def preview_image(
    image_bytes: bytes,
    filename: str,
    target_width_mm: float | None = None,
    target_height_mm: float | None = None,
) -> dict:
    """Full pipeline: image bytes to SVG preview + stats."""
    img = _decode_image(image_bytes)
    h, w = img.shape[:2]
    image_type = classify_image(img)
    binary = preprocess_image(img, image_type)
    paths = trace_bitmap(binary)
    polylines = flatten_paths(paths)
    scale = _compute_scale(w, h, target_width_mm, target_height_mm)
    point_count = sum(len(pl) for pl in polylines)
    svg = write_svg(polylines, width=w, height=h, scale_factor=scale)
    return {
        "svg": svg,
        "stats": {
            "path_count": len(polylines),
            "point_count": point_count,
            "width_mm": w * scale,
            "height_mm": h * scale,
        },
    }
