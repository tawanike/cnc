# Image to DXF Converter — Design Document

## Problem

Convert PNG/JPEG images (both clean line art and photos of physical parts) to DXF files suitable for CNC workflows.

## Solution

A single-page web app with a Python backend. User uploads an image, optionally sets a target scale, and gets a DXF file download.

## Architecture

```
Browser (HTML/CSS/JS)
  ├── Drag-and-drop image upload
  ├── Scale input (target width/height in mm)
  ├── SVG preview of traced result overlaid on original
  └── DXF download button
        │
        ▼
FastAPI Backend
  ├── POST /api/convert — accepts image + scale params, returns DXF
  ├── GET /api/preview — accepts image + scale params, returns SVG preview
  └── Static file serving for frontend
        │
        ▼
Processing Pipeline
  1. Load image (PNG/JPEG)
  2. Auto-classify: line art vs photo
  3. Preprocess (strategy per image type)
  4. Trace with Potrace → Bezier paths
  5. Flatten Beziers → polylines (0.1mm tolerance)
  6. Scale to real-world units
  7. Write DXF with ezdxf
```

## Processing Pipeline Detail

### Image Classification
- Compute histogram of grayscale image
- Line art: bimodal distribution (mostly black + white pixels)
- Photo: spread distribution across intensity range
- Simple heuristic: if >70% of pixels are within 20% of black or white → line art

### Preprocessing — Line Art
1. Grayscale conversion
2. Otsu's threshold (automatic optimal threshold)
3. Optional: morphological close to fill small gaps

### Preprocessing — Photos
1. Grayscale conversion
2. Gaussian blur (σ=2) to reduce noise
3. Adaptive threshold (block size=11, C=2)
4. Morphological open to remove noise
5. Morphological close to fill gaps

### Tracing
- Feed binary bitmap to Potrace
- Potrace outputs Bezier curve paths (cubic splines)

### Bezier to Polyline Conversion
- Recursive subdivision of cubic Bezier curves
- Flatness tolerance: 0.1mm (CNC-appropriate)
- Each Bezier curve becomes a series of line segments

### Scaling
- Default: 1 pixel = 1mm
- User can specify target width or height in mm
- Aspect ratio always preserved

### DXF Output
- Use `ezdxf` library
- Write LWPOLYLINE entities (one per traced path)
- All geometry in modelspace
- Units set to millimeters

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React (Vite + TypeScript) |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Image processing | OpenCV (cv2) |
| Tracing | Potrace (via pypotrace or subprocess) |
| DXF generation | ezdxf |
| Preview | SVG generated server-side |

## Project Structure

```
cnc/
├── backend/
│   ├── main.py              # FastAPI app, routes
│   ├── pipeline.py           # Image processing pipeline
│   ├── classify.py           # Line art vs photo classification
│   ├── preprocess.py         # Preprocessing strategies
│   ├── trace.py              # Potrace wrapper
│   ├── bezier.py             # Bezier to polyline conversion
│   ├── dxf_writer.py         # DXF file generation
│   └── requirements.txt
├── frontend/               # React (Vite + TypeScript)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── components/
│   │       ├── DropZone.tsx
│   │       ├── Preview.tsx
│   │       └── ScaleInput.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── tests/
│   ├── test_classify.py
│   ├── test_preprocess.py
│   ├── test_pipeline.py
│   └── fixtures/             # Test images
└── docs/
    └── plans/
```

## API

### POST /api/convert
- **Input:** multipart form — `image` (file), `target_width_mm` (optional float), `target_height_mm` (optional float)
- **Output:** DXF file download (`application/dxf`)

### POST /api/preview
- **Input:** same as /api/convert
- **Output:** JSON with `svg` (traced paths as SVG string), `stats` (path count, point count, dimensions)

## Scope — What's NOT in v1

- Centerline tracing (outline only)
- Multi-layer DXF output
- Color-based layer separation
- User-adjustable tracing parameters (smart defaults only)
- User accounts or saved history
