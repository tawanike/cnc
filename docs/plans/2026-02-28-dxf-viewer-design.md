# DXF Viewer — Design Document

## Problem

After converting an image to DXF, there's no way to view the result in the app. Users must download the file and open it in external software.

## Solution

A reusable client-side DXF viewer component that parses DXF files in the browser and renders them as interactive SVG. Used in two places:

1. **Inline after conversion** — shows the converted DXF alongside the existing SVG preview
2. **Standalone viewer** — a separate tab/page where users can open any .dxf file from disk

## Architecture

```
DXF content (string)
  ↓
dxf-parser (npm library)
  ↓
Extract LWPOLYLINE entities
  ↓
Compute bounding box (viewBox)
  ↓
Render as <svg> with <polyline> elements
  ↓
Pan/zoom via viewBox manipulation (mouse wheel + drag)
```

No backend changes required. All parsing and rendering happens client-side.

## Components

### DxfViewer

Reusable component. Props: `dxfContent: string`.

- Parses DXF with `dxf-parser`
- Extracts LWPOLYLINE entities from the parsed structure
- Computes bounding box from all vertices
- Renders SVG with polyline elements
- Pan: mouse drag updates viewBox origin
- Zoom: mouse wheel scales viewBox dimensions

### Converter integration

After the `/api/convert` call succeeds, decode the DXF blob to text and pass it to `DxfViewer`. Show it below the existing SVG preview with a label like "DXF Output".

### Standalone viewer

A tab or simple route (`/viewer`) with:
- A file drop zone (reuse DropZone pattern but accept .dxf files)
- The DxfViewer component rendering the loaded file

## Navigation

Simple tab-style navigation at the top: "Converter" | "DXF Viewer". No router library needed — just conditional rendering with state.

## Tech

- `dxf-parser` npm package for parsing DXF files
- SVG for rendering (matches existing preview approach)
- Mouse events for pan/zoom

## Scope — What's NOT included

- 3D viewing
- Entity types beyond LWPOLYLINE (LINE, ARC, CIRCLE could be added later)
- Measurement tools
- Layer visibility toggles
