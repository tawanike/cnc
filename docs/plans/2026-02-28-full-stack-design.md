# Full Stack End-to-End — Design Document

## Goal

Wire together the existing backend pipeline modules into a FastAPI API, build a React frontend, and deliver a working image-to-DXF converter web app.

## Backend

### Pipeline Orchestrator (`backend/pipeline.py`)

Single entry points that chain the existing modules:

- `convert_image(image_bytes, filename, target_width_mm, target_height_mm) -> bytes` — returns DXF file bytes
- `preview_image(image_bytes, filename, target_width_mm, target_height_mm) -> dict` — returns SVG string + stats

Flow: decode image → classify → preprocess → trace → flatten beziers → scale → write DXF (or SVG).

### SVG Writer (`backend/svg_writer.py`)

Takes polylines (same format as dxf_writer) and produces an SVG string. Used for preview overlay.

### FastAPI App (`backend/main.py`)

- `POST /api/convert` — multipart form: `image` (file), `target_width_mm` (optional float), `target_height_mm` (optional float). Returns DXF file download (`application/dxf`).
- `POST /api/preview` — same input. Returns JSON: `{ svg: string, stats: { path_count, point_count, width_mm, height_mm } }`.
- Static file serving for frontend build output.

### Scaling Logic

- Default: 1 pixel = 1mm
- If `target_width_mm` provided: `scale = target_width_mm / image_width_px`
- If `target_height_mm` provided: `scale = target_height_mm / image_height_px`
- If both provided: use width (ignore height to preserve aspect ratio)
- Scale factor is passed to dxf_writer and svg_writer

## Frontend

React + Vite + TypeScript. Single page, no routing.

### Components

- **DropZone** — Drag-and-drop or click-to-upload PNG/JPEG. Shows uploaded image thumbnail.
- **ScaleInput** — Optional target width/height in mm. Auto-calculates the other dimension to preserve aspect ratio.
- **Preview** — Calls `/api/preview` on upload, overlays traced SVG on the original image.
- **Download button** — Calls `/api/convert`, triggers DXF file download.

### Flow

1. User drops/selects an image
2. Frontend immediately calls `/api/preview` to show traced paths
3. User optionally adjusts scale
4. Scale change re-triggers preview
5. User clicks Download → calls `/api/convert` → browser downloads DXF

## Not In Scope

- Centerline tracing
- Multi-layer DXF
- Color-based separation
- User-adjustable tracing parameters
- User accounts
