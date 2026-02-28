# Full Stack End-to-End Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire the existing backend pipeline into a FastAPI API with SVG preview, and build a React frontend for image upload, preview, and DXF download.

**Architecture:** React (Vite + TypeScript) frontend sends images to a FastAPI backend. The backend chains existing modules (classify → preprocess → trace → flatten → write) through a pipeline orchestrator. Two endpoints: `/api/convert` returns DXF bytes, `/api/preview` returns SVG + stats JSON. Frontend shows drag-and-drop upload, SVG overlay preview, scale controls, and download button.

**Tech Stack:** Python 3.12, FastAPI, existing backend modules, React, Vite, TypeScript

---

### Task 1: SVG writer module

**Files:**
- Create: `backend/svg_writer.py`
- Create: `tests/test_svg_writer.py`

**Step 1: Write failing tests**

```python
# tests/test_svg_writer.py
from backend.svg_writer import write_svg


def test_write_svg_returns_string():
    polylines = [[(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]]
    result = write_svg(polylines, width=100, height=100)
    assert isinstance(result, str)
    assert "<svg" in result


def test_write_svg_contains_polyline():
    polylines = [[(0, 0), (50, 50), (100, 0)]]
    result = write_svg(polylines, width=100, height=100)
    assert "<polyline" in result
    assert "0,0" in result


def test_write_svg_multiple_polylines():
    polylines = [
        [(0, 0), (50, 0)],
        [(60, 60), (100, 100)],
    ]
    result = write_svg(polylines, width=100, height=100)
    assert result.count("<polyline") == 2


def test_write_svg_with_scale():
    polylines = [[(0, 0), (10, 0), (10, 10)]]
    result = write_svg(polylines, width=10, height=10, scale_factor=2.0)
    assert "20,0" in result


def test_write_svg_empty():
    result = write_svg([], width=100, height=100)
    assert "<svg" in result
    assert "<polyline" not in result
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_svg_writer.py -v`
Expected: FAIL with ImportError

**Step 3: Implement SVG writer**

```python
# backend/svg_writer.py


def write_svg(
    polylines: list[list[tuple[float, float]]],
    width: float,
    height: float,
    scale_factor: float = 1.0,
) -> str:
    """Write polylines to an SVG string."""
    sw = width * scale_factor
    sh = height * scale_factor
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {sw} {sh}" width="{sw}" height="{sh}">'
    ]
    for polyline in polylines:
        if len(polyline) < 2:
            continue
        points_str = " ".join(
            f"{x * scale_factor},{y * scale_factor}" for x, y in polyline
        )
        parts.append(
            f'<polyline points="{points_str}" '
            f'fill="none" stroke="red" stroke-width="1"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_svg_writer.py -v`
Expected: All 5 PASS

**Step 5: Commit**

```bash
git add backend/svg_writer.py tests/test_svg_writer.py
git commit -m "feat: SVG writer for preview overlay"
```

---

### Task 2: Pipeline orchestrator

**Files:**
- Create: `backend/pipeline.py`
- Create: `tests/test_pipeline.py`

**Step 1: Write failing tests**

```python
# tests/test_pipeline.py
import numpy as np
from PIL import Image
import io

from backend.pipeline import convert_image, preview_image


def _make_test_png() -> bytes:
    """Create a simple black-square-on-white PNG."""
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


def test_convert_image_returns_dxf_bytes():
    png_bytes = _make_test_png()
    result = convert_image(png_bytes, "test.png")
    assert isinstance(result, bytes)
    assert b"LWPOLYLINE" in result


def test_convert_image_with_target_width():
    png_bytes = _make_test_png()
    result = convert_image(png_bytes, "test.png", target_width_mm=200.0)
    assert isinstance(result, bytes)


def test_preview_image_returns_svg_and_stats():
    png_bytes = _make_test_png()
    result = preview_image(png_bytes, "test.png")
    assert "svg" in result
    assert "<svg" in result["svg"]
    assert "stats" in result
    assert "path_count" in result["stats"]
    assert "width_mm" in result["stats"]
    assert "height_mm" in result["stats"]


def test_convert_image_invalid_format():
    """Non-image bytes should raise ValueError."""
    import pytest
    with pytest.raises(ValueError, match="decode"):
        convert_image(b"not an image", "bad.png")
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipeline.py -v`
Expected: FAIL with ImportError

**Step 3: Implement pipeline**

```python
# backend/pipeline.py
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_pipeline.py -v`
Expected: All 4 PASS

**Step 5: Commit**

```bash
git add backend/pipeline.py tests/test_pipeline.py
git commit -m "feat: pipeline orchestrator for convert and preview"
```

---

### Task 3: FastAPI app

**Files:**
- Create: `backend/main.py`
- Create: `tests/test_main.py`

**Step 1: Write failing tests**

```python
# tests/test_main.py
import io
import numpy as np
from PIL import Image
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


def _make_test_png() -> bytes:
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_convert_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png, "image/png")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert b"LWPOLYLINE" in response.content


@pytest.mark.asyncio
async def test_convert_with_scale():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png, "image/png")},
            data={"target_width_mm": "200"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_preview_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/preview",
            files={"image": ("test.png", png, "image/png")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert "<svg" in data["svg"]
    assert "stats" in data
    assert data["stats"]["path_count"] > 0


@pytest.mark.asyncio
async def test_convert_no_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/convert")
    assert response.status_code == 422
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with ImportError

**Step 3: Implement FastAPI app**

```python
# backend/main.py
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response

from backend.pipeline import convert_image, preview_image

app = FastAPI()


@app.post("/api/convert")
async def convert(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = await image.read()
    dxf_bytes = convert_image(
        image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
    )
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": "attachment; filename=output.dxf"},
    )


@app.post("/api/preview")
async def preview(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = await image.read()
    return preview_image(
        image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
    )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v`
Expected: All 4 PASS

**Step 5: Run full test suite**

Run: `pytest -v`
Expected: All tests PASS (19 existing + 4 pipeline + 5 svg_writer + 4 API = 32)

**Step 6: Commit**

```bash
git add backend/main.py tests/test_main.py
git commit -m "feat: FastAPI endpoints for convert and preview"
```

---

### Task 4: React frontend scaffolding

**Files:**
- Create: `frontend/` directory via Vite

**Step 1: Scaffold Vite + React + TypeScript project**

```bash
cd /home/tawanda/dev/amengineering/cnc
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

**Step 2: Configure Vite proxy to backend**

Replace `frontend/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
```

**Step 3: Clean up scaffolded files**

- Delete `frontend/src/App.css` contents (will replace)
- Delete `frontend/src/assets/` directory
- Replace `frontend/src/index.css` with minimal reset

```css
/* frontend/src/index.css */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  color: #1a1a1a;
  background: #fafafa;
}
```

**Step 4: Verify dev server starts**

Run: `cd frontend && npm run dev` (stop after confirming it starts)

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with Vite"
```

---

### Task 5: DropZone component

**Files:**
- Create: `frontend/src/components/DropZone.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create DropZone component**

```tsx
// frontend/src/components/DropZone.tsx
import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";

interface DropZoneProps {
  onFileSelect: (file: File) => void;
}

export function DropZone({ onFileSelect }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.type.startsWith("image/")) return;
      setPreview(URL.createObjectURL(file));
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const onDragLeave = useCallback(() => setDragging(false), []);

  const onChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      style={{
        border: `2px dashed ${dragging ? "#2563eb" : "#d1d5db"}`,
        borderRadius: 8,
        padding: 40,
        textAlign: "center",
        cursor: "pointer",
        background: dragging ? "#eff6ff" : "white",
        transition: "all 0.15s",
      }}
      onClick={() => document.getElementById("file-input")?.click()}
    >
      <input
        id="file-input"
        type="file"
        accept="image/png,image/jpeg"
        onChange={onChange}
        style={{ display: "none" }}
      />
      {preview ? (
        <img
          src={preview}
          alt="Uploaded"
          style={{ maxWidth: "100%", maxHeight: 300 }}
        />
      ) : (
        <p>Drop a PNG or JPEG here, or click to select</p>
      )}
    </div>
  );
}
```

**Step 2: Wire into App.tsx**

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { DropZone } from "./components/DropZone";

function App() {
  const [file, setFile] = useState<File | null>(null);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <DropZone onFileSelect={setFile} />
      {file && <p>Selected: {file.name}</p>}
    </div>
  );
}

export default App;
```

**Step 3: Verify in browser**

Run: `cd frontend && npm run dev`
Open browser, verify drop zone renders. Drop an image, verify thumbnail shows.

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: DropZone component with drag-and-drop upload"
```

---

### Task 6: ScaleInput component

**Files:**
- Create: `frontend/src/components/ScaleInput.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Create ScaleInput component**

```tsx
// frontend/src/components/ScaleInput.tsx
import { type ChangeEvent } from "react";

interface ScaleInputProps {
  targetWidthMm: string;
  targetHeightMm: string;
  onWidthChange: (value: string) => void;
  onHeightChange: (value: string) => void;
}

export function ScaleInput({
  targetWidthMm,
  targetHeightMm,
  onWidthChange,
  onHeightChange,
}: ScaleInputProps) {
  return (
    <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 16 }}>
      <label>
        Width (mm):
        <input
          type="number"
          min="0"
          step="any"
          value={targetWidthMm}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            onWidthChange(e.target.value);
            onHeightChange("");
          }}
          placeholder="auto"
          style={{ marginLeft: 8, width: 100, padding: 4 }}
        />
      </label>
      <label>
        Height (mm):
        <input
          type="number"
          min="0"
          step="any"
          value={targetHeightMm}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            onHeightChange(e.target.value);
            onWidthChange("");
          }}
          placeholder="auto"
          style={{ marginLeft: 8, width: 100, padding: 4 }}
        />
      </label>
    </div>
  );
}
```

**Step 2: Wire into App.tsx**

Update `App.tsx` to add scale state and component:

```tsx
// frontend/src/App.tsx
import { useState } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetWidthMm, setTargetWidthMm] = useState("");
  const [targetHeightMm, setTargetHeightMm] = useState("");

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <DropZone onFileSelect={setFile} />
      {file && (
        <>
          <ScaleInput
            targetWidthMm={targetWidthMm}
            targetHeightMm={targetHeightMm}
            onWidthChange={setTargetWidthMm}
            onHeightChange={setTargetHeightMm}
          />
        </>
      )}
    </div>
  );
}

export default App;
```

**Step 3: Verify in browser**

Verify scale inputs appear after image is selected.

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: ScaleInput component for target dimensions"
```

---

### Task 7: Preview component and API integration

**Files:**
- Create: `frontend/src/components/Preview.tsx`
- Create: `frontend/src/api.ts`
- Modify: `frontend/src/App.tsx`

**Step 1: Create API helper**

```typescript
// frontend/src/api.ts
export interface PreviewResult {
  svg: string;
  stats: {
    path_count: number;
    point_count: number;
    width_mm: number;
    height_mm: number;
  };
}

export async function fetchPreview(
  file: File,
  targetWidthMm?: number,
  targetHeightMm?: number
): Promise<PreviewResult> {
  const form = new FormData();
  form.append("image", file);
  if (targetWidthMm) form.append("target_width_mm", String(targetWidthMm));
  if (targetHeightMm) form.append("target_height_mm", String(targetHeightMm));

  const res = await fetch("/api/preview", { method: "POST", body: form });
  if (!res.ok) throw new Error(`Preview failed: ${res.status}`);
  return res.json();
}

export async function fetchConvert(
  file: File,
  targetWidthMm?: number,
  targetHeightMm?: number
): Promise<Blob> {
  const form = new FormData();
  form.append("image", file);
  if (targetWidthMm) form.append("target_width_mm", String(targetWidthMm));
  if (targetHeightMm) form.append("target_height_mm", String(targetHeightMm));

  const res = await fetch("/api/convert", { method: "POST", body: form });
  if (!res.ok) throw new Error(`Convert failed: ${res.status}`);
  return res.blob();
}
```

**Step 2: Create Preview component**

```tsx
// frontend/src/components/Preview.tsx
interface PreviewProps {
  svgContent: string;
  stats: {
    path_count: number;
    point_count: number;
    width_mm: number;
    height_mm: number;
  };
}

export function Preview({ svgContent, stats }: PreviewProps) {
  return (
    <div style={{ marginTop: 16 }}>
      <div
        dangerouslySetInnerHTML={{ __html: svgContent }}
        style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 8, background: "white" }}
      />
      <div style={{ marginTop: 8, fontSize: 14, color: "#6b7280" }}>
        {stats.path_count} paths, {stats.point_count} points —{" "}
        {stats.width_mm.toFixed(1)} × {stats.height_mm.toFixed(1)} mm
      </div>
    </div>
  );
}
```

**Step 3: Wire everything into App.tsx**

```tsx
// frontend/src/App.tsx
import { useState, useEffect, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";
import { Preview } from "./components/Preview";
import { fetchPreview, fetchConvert, type PreviewResult } from "./api";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [targetWidthMm, setTargetWidthMm] = useState("");
  const [targetHeightMm, setTargetHeightMm] = useState("");
  const [previewData, setPreviewData] = useState<PreviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) return;
    setLoading(true);
    setError(null);
    const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
    const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
    fetchPreview(file, widthNum, heightNum)
      .then(setPreviewData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [file, targetWidthMm, targetHeightMm]);

  const handleDownload = useCallback(async () => {
    if (!file) return;
    setError(null);
    const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
    const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
    try {
      const blob = await fetchConvert(file, widthNum, heightNum);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = file.name.replace(/\.\w+$/, ".dxf");
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    }
  }, [file, targetWidthMm, targetHeightMm]);

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <DropZone onFileSelect={setFile} />
      {file && (
        <>
          <ScaleInput
            targetWidthMm={targetWidthMm}
            targetHeightMm={targetHeightMm}
            onWidthChange={setTargetWidthMm}
            onHeightChange={setTargetHeightMm}
          />
          {loading && <p style={{ marginTop: 16 }}>Processing...</p>}
          {error && <p style={{ marginTop: 16, color: "red" }}>{error}</p>}
          {previewData && <Preview svgContent={previewData.svg} stats={previewData.stats} />}
          <button
            onClick={handleDownload}
            disabled={!previewData}
            style={{
              marginTop: 16,
              padding: "10px 24px",
              fontSize: 16,
              background: previewData ? "#2563eb" : "#d1d5db",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: previewData ? "pointer" : "not-allowed",
            }}
          >
            Download DXF
          </button>
        </>
      )}
    </div>
  );
}

export default App;
```

**Step 4: Verify in browser**

Run backend: `cd /home/tawanda/dev/amengineering/cnc && uvicorn backend.main:app --reload`
Run frontend: `cd frontend && npm run dev`
Upload an image, verify SVG preview shows, download DXF.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: Preview component, API integration, and download"
```

---

### Task 8: Static file serving for production

**Files:**
- Modify: `backend/main.py`

**Step 1: Add static file serving**

Add to `backend/main.py` after the route definitions:

```python
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Serve frontend build if it exists (production)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
```

**Step 2: Build frontend**

```bash
cd frontend && npm run build
```

**Step 3: Test production mode**

Run: `uvicorn backend.main:app`
Open `http://localhost:8000` — should serve the React app.

**Step 4: Commit**

```bash
git add backend/main.py
git commit -m "feat: serve frontend static build in production"
```

---

### Task 9: End-to-end verification

**Step 1: Run full backend test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Manual end-to-end test**

Start backend: `uvicorn backend.main:app --reload`
Start frontend: `cd frontend && npm run dev`

1. Open browser to `http://localhost:5173`
2. Drop a PNG/JPEG image
3. Verify SVG preview appears
4. Set target width to 200mm
5. Verify preview updates
6. Click Download DXF
7. Open DXF in a viewer to verify geometry

**Step 3: Final commit if any fixes needed**
