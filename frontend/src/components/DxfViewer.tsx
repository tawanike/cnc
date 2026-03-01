import { useMemo, useState, useEffect, useCallback, useRef, type WheelEvent, type MouseEvent } from "react";
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

    // First pass: collect raw vertices and find Y range for flipping
    const rawLines: { x: number; y: number }[][] = [];
    let rawMinY = Infinity, rawMaxY = -Infinity;
    for (const entity of parsed.entities) {
      if (entity.vertices && entity.vertices.length >= 2) {
        const verts = entity.vertices.map((v) => ({ x: v.x, y: v.y }));
        for (const v of verts) {
          if (v.y < rawMinY) rawMinY = v.y;
          if (v.y > rawMaxY) rawMaxY = v.y;
        }
        rawLines.push(verts);
      }
    }

    if (rawLines.length === 0) {
      return { polylines: [], bounds: { minX: 0, minY: 0, maxX: 100, maxY: 100 } };
    }

    // Second pass: flip Y (DXF is Y-up, SVG is Y-down) and compute final bounds
    const lines: { x: number; y: number }[][] = [];
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const raw of rawLines) {
      const flipped = raw.map((v) => ({ x: v.x, y: rawMinY + rawMaxY - v.y }));
      for (const v of flipped) {
        if (v.x < minX) minX = v.x;
        if (v.y < minY) minY = v.y;
        if (v.x > maxX) maxX = v.x;
        if (v.y > maxY) maxY = v.y;
      }
      lines.push(flipped);
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
  useEffect(() => setViewBox(initialViewBox), [initialViewBox]);

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

  return (
    <svg
      ref={svgRef}
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
      preserveAspectRatio="xMidYMid meet"
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
      {polylines.map((pl, i) => (
        <polyline
          key={i}
          points={pl.map((v) => `${v.x},${v.y}`).join(" ")}
          fill="none"
          stroke="#2563eb"
          strokeWidth={viewBox.width / 500}
        />
      ))}
    </svg>
  );
}
