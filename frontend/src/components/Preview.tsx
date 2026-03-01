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
