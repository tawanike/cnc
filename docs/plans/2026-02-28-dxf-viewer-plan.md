# DXF Viewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a client-side DXF viewer with pan/zoom, integrated both inline after conversion and as a standalone viewer tab.

**Architecture:** A reusable `DxfViewer` React component parses DXF text with `dxf-parser`, extracts LWPOLYLINE entities, and renders them as SVG with mouse-driven pan/zoom. The app gets tab navigation (Converter | Viewer) via simple state toggle. The converter page shows DXF output inline after conversion. The viewer page accepts .dxf files dropped from disk.

**Tech Stack:** React, TypeScript, dxf-parser (npm), SVG

---

### Task 1: Install dxf-parser and add type declaration

**Files:**
- Modify: `frontend/package.json` (via npm install)
- Create: `frontend/src/dxf-parser.d.ts`

**Step 1: Install dxf-parser**

```bash
cd /home/tawanda/dev/amengineering/cnc/frontend
npm install dxf-parser
```

**Step 2: Create type declaration**

The `dxf-parser` package does not ship TypeScript types. Create a minimal declaration for what we use:

```typescript
// frontend/src/dxf-parser.d.ts
declare module "dxf-parser" {
  interface LWPolylineVertex {
    x: number;
    y: number;
  }

  interface LWPolylineEntity {
    type: "LWPOLYLINE";
    vertices: LWPolylineVertex[];
    shape: boolean;
  }

  interface LineEntity {
    type: "LINE";
    vertices: [{ x: number; y: number }, { x: number; y: number }];
  }

  interface DxfEntity {
    type: string;
    vertices?: { x: number; y: number }[];
    shape?: boolean;
  }

  interface DxfResult {
    entities: DxfEntity[];
  }

  export default class DxfParser {
    parseSync(content: string): DxfResult;
  }
}
```

**Step 3: Verify build**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
cd /home/tawanda/dev/amengineering/cnc
git add frontend/package.json frontend/package-lock.json frontend/src/dxf-parser.d.ts
git commit -m "feat: add dxf-parser dependency with type declarations"
```

---

### Task 2: DxfViewer component

**Files:**
- Create: `frontend/src/components/DxfViewer.tsx`

**Step 1: Create DxfViewer component**

```tsx
// frontend/src/components/DxfViewer.tsx
import { useMemo, useState, useCallback, useRef, type WheelEvent, type MouseEvent } from "react";
import DxfParser from "dxf-parser";

interface DxfViewerProps {
  dxfContent: string;
}

interface ViewBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export function DxfViewer({ dxfContent }: DxfViewerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const { polylines, bounds } = useMemo(() => {
    const parser = new DxfParser();
    let parsed;
    try {
      parsed = parser.parseSync(dxfContent);
    } catch {
      return { polylines: [], bounds: { minX: 0, minY: 0, maxX: 100, maxY: 100 } };
    }

    const lines: { x: number; y: number }[][] = [];
    for (const entity of parsed.entities) {
      if (entity.vertices && entity.vertices.length >= 2) {
        lines.push(entity.vertices.map((v) => ({ x: v.x, y: v.y })));
      }
    }

    if (lines.length === 0) {
      return { polylines: [], bounds: { minX: 0, minY: 0, maxX: 100, maxY: 100 } };
    }

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const line of lines) {
      for (const v of line) {
        if (v.x < minX) minX = v.x;
        if (v.y < minY) minY = v.y;
        if (v.x > maxX) maxX = v.x;
        if (v.y > maxY) maxY = v.y;
      }
    }

    return { polylines: lines, bounds: { minX, minY, maxX, maxY } };
  }, [dxfContent]);

  const initialViewBox = useMemo((): ViewBox => {
    const padding = 10;
    const w = bounds.maxX - bounds.minX || 100;
    const h = bounds.maxY - bounds.minY || 100;
    return {
      x: bounds.minX - padding,
      y: bounds.minY - padding,
      width: w + padding * 2,
      height: h + padding * 2,
    };
  }, [bounds]);

  const [viewBox, setViewBox] = useState<ViewBox>(initialViewBox);

  // Reset viewBox when content changes
  useMemo(() => setViewBox(initialViewBox), [initialViewBox]);

  const onWheel = useCallback((e: WheelEvent<SVGSVGElement>) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.1 : 0.9;
    setViewBox((vb) => {
      const cx = vb.x + vb.width / 2;
      const cy = vb.y + vb.height / 2;
      const newW = vb.width * factor;
      const newH = vb.height * factor;
      return { x: cx - newW / 2, y: cy - newH / 2, width: newW, height: newH };
    });
  }, []);

  const onMouseDown = useCallback((e: MouseEvent<SVGSVGElement>) => {
    setDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  }, []);

  const onMouseMove = useCallback(
    (e: MouseEvent<SVGSVGElement>) => {
      if (!dragging || !svgRef.current) return;
      const svg = svgRef.current;
      const rect = svg.getBoundingClientRect();
      const dx = ((e.clientX - dragStart.x) / rect.width) * viewBox.width;
      const dy = ((e.clientY - dragStart.y) / rect.height) * viewBox.height;
      setViewBox((vb) => ({ ...vb, x: vb.x - dx, y: vb.y - dy }));
      setDragStart({ x: e.clientX, y: e.clientY });
    },
    [dragging, dragStart, viewBox.width, viewBox.height]
  );

  const onMouseUp = useCallback(() => setDragging(false), []);

  if (polylines.length === 0) {
    return <p style={{ marginTop: 16, color: "#6b7280" }}>No geometry found in DXF file.</p>;
  }

  // DXF uses Y-up, SVG uses Y-down. Flip with a transform.
  const flipY = bounds.minY + bounds.maxY;

  return (
    <svg
      ref={svgRef}
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
      style={{
        width: "100%",
        height: 400,
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        background: "white",
        cursor: dragging ? "grabbing" : "grab",
      }}
      onWheel={onWheel}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      <g transform={`scale(1,-1) translate(0,${-flipY})`}>
        {polylines.map((pl, i) => (
          <polyline
            key={i}
            points={pl.map((v) => `${v.x},${v.y}`).join(" ")}
            fill="none"
            stroke="#2563eb"
            strokeWidth={viewBox.width / 500}
          />
        ))}
      </g>
    </svg>
  );
}
```

**Step 2: Verify build**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
cd /home/tawanda/dev/amengineering/cnc
git add frontend/src/components/DxfViewer.tsx
git commit -m "feat: DxfViewer component with pan/zoom"
```

---

### Task 3: Integrate DXF viewer inline after conversion

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Update App.tsx to show DXF viewer after conversion**

Currently, `handleDownload` converts and immediately triggers download. Change it to also store the DXF text so the viewer can render it.

Add state:
```tsx
const [dxfContent, setDxfContent] = useState<string | null>(null);
```

Update `handleDownload` to decode the blob and store it:
```tsx
const handleDownload = useCallback(async () => {
    if (!file) return;
    setError(null);
    const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
    const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
    try {
      const blob = await fetchConvert(file, widthNum, heightNum);
      const text = await blob.text();
      setDxfContent(text);
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
```

Add DxfViewer import and render it below the download button:
```tsx
import { DxfViewer } from "./components/DxfViewer";

// In the JSX, after the download button:
{dxfContent && (
  <div style={{ marginTop: 16 }}>
    <h3>DXF Output</h3>
    <DxfViewer dxfContent={dxfContent} />
  </div>
)}
```

Also reset `dxfContent` when file changes — add `setDxfContent(null)` inside the existing `useEffect` before the `setTimeout`.

**Step 2: Verify build**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
cd /home/tawanda/dev/amengineering/cnc
git add frontend/src/App.tsx
git commit -m "feat: inline DXF viewer after conversion"
```

---

### Task 4: DxfDropZone component for standalone viewer

**Files:**
- Create: `frontend/src/components/DxfDropZone.tsx`

**Step 1: Create the DXF file drop zone**

This is similar to the image DropZone but accepts .dxf files and reads them as text.

```tsx
// frontend/src/components/DxfDropZone.tsx
import { useCallback, useState, type DragEvent, type ChangeEvent } from "react";

interface DxfDropZoneProps {
  onFileLoad: (content: string, filename: string) => void;
}

export function DxfDropZone({ onFileLoad }: DxfDropZoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          onFileLoad(reader.result, file.name);
        }
      };
      reader.readAsText(file);
    },
    [onFileLoad]
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
      onClick={() => document.getElementById("dxf-file-input")?.click()}
    >
      <input
        id="dxf-file-input"
        type="file"
        accept=".dxf"
        onChange={onChange}
        style={{ display: "none" }}
      />
      <p>Drop a .dxf file here, or click to select</p>
    </div>
  );
}
```

**Step 2: Verify build**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
cd /home/tawanda/dev/amengineering/cnc
git add frontend/src/components/DxfDropZone.tsx
git commit -m "feat: DxfDropZone component for loading DXF files"
```

---

### Task 5: Tab navigation and standalone viewer page

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add tab navigation and viewer page**

Refactor App.tsx to have two tabs: "Converter" and "DXF Viewer". Use a state variable `tab` to toggle between them. Extract the existing converter UI into a section, and add a new viewer section.

Replace `frontend/src/App.tsx` entirely:

```tsx
// frontend/src/App.tsx
import { useState, useEffect, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";
import { Preview } from "./components/Preview";
import { DxfViewer } from "./components/DxfViewer";
import { DxfDropZone } from "./components/DxfDropZone";
import { fetchPreview, fetchConvert, type PreviewResult } from "./api";

type Tab = "converter" | "viewer";

function App() {
  const [tab, setTab] = useState<Tab>("converter");

  // Converter state
  const [file, setFile] = useState<File | null>(null);
  const [targetWidthMm, setTargetWidthMm] = useState("");
  const [targetHeightMm, setTargetHeightMm] = useState("");
  const [previewData, setPreviewData] = useState<PreviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dxfContent, setDxfContent] = useState<string | null>(null);

  // Viewer state
  const [viewerDxf, setViewerDxf] = useState<string | null>(null);
  const [viewerFilename, setViewerFilename] = useState<string | null>(null);

  useEffect(() => {
    if (!file) return;
    setDxfContent(null);
    const timeoutId = setTimeout(() => {
      setLoading(true);
      setError(null);
      const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
      const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
      fetchPreview(file, widthNum, heightNum)
        .then(setPreviewData)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 400);
    return () => clearTimeout(timeoutId);
  }, [file, targetWidthMm, targetHeightMm]);

  const handleDownload = useCallback(async () => {
    if (!file) return;
    setError(null);
    const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
    const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
    try {
      const blob = await fetchConvert(file, widthNum, heightNum);
      const text = await blob.text();
      setDxfContent(text);
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

  const handleViewerFileLoad = useCallback((content: string, filename: string) => {
    setViewerDxf(content);
    setViewerFilename(filename);
  }, []);

  const tabStyle = (t: Tab) => ({
    padding: "8px 20px",
    fontSize: 16,
    border: "none",
    borderBottom: tab === t ? "2px solid #2563eb" : "2px solid transparent",
    background: "none",
    color: tab === t ? "#2563eb" : "#6b7280",
    cursor: "pointer" as const,
    fontWeight: tab === t ? 600 : 400,
  });

  return (
    <div style={{ maxWidth: 800, margin: "40px auto", padding: "0 20px" }}>
      <h1>Image to DXF Converter</h1>
      <nav style={{ display: "flex", gap: 4, borderBottom: "1px solid #e5e7eb", marginBottom: 20 }}>
        <button style={tabStyle("converter")} onClick={() => setTab("converter")}>
          Converter
        </button>
        <button style={tabStyle("viewer")} onClick={() => setTab("viewer")}>
          DXF Viewer
        </button>
      </nav>

      {tab === "converter" && (
        <>
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
              {dxfContent && (
                <div style={{ marginTop: 16 }}>
                  <h3>DXF Output</h3>
                  <DxfViewer dxfContent={dxfContent} />
                </div>
              )}
            </>
          )}
        </>
      )}

      {tab === "viewer" && (
        <>
          <DxfDropZone onFileLoad={handleViewerFileLoad} />
          {viewerFilename && (
            <p style={{ marginTop: 8, fontSize: 14, color: "#6b7280" }}>{viewerFilename}</p>
          )}
          {viewerDxf && (
            <div style={{ marginTop: 16 }}>
              <DxfViewer dxfContent={viewerDxf} />
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;
```

**Step 2: Verify build**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
cd /home/tawanda/dev/amengineering/cnc
git add frontend/src/App.tsx
git commit -m "feat: tab navigation with converter and standalone DXF viewer"
```

---

### Task 6: End-to-end verification

**Step 1: Run backend tests**

Run: `cd /home/tawanda/dev/amengineering/cnc && pytest -v`
Expected: All 34 tests pass

**Step 2: Build frontend**

Run: `cd /home/tawanda/dev/amengineering/cnc/frontend && npm run build`
Expected: Build succeeds

**Step 3: Manual test — converter flow**

Start backend: `uvicorn backend.main:app --reload`
Start frontend: `cd frontend && npm run dev`

1. Open http://localhost:5173
2. On the Converter tab, upload a PNG/JPEG
3. Verify SVG preview appears
4. Click "Download DXF"
5. Verify DXF file downloads AND the DXF Output viewer appears inline showing the geometry
6. Verify pan (drag) and zoom (scroll) work in the viewer

**Step 4: Manual test — standalone viewer**

1. Click the "DXF Viewer" tab
2. Drop the DXF file you just downloaded
3. Verify the geometry renders
4. Verify pan/zoom work
