// frontend/src/App.tsx
import { useState, useEffect, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { ScaleInput } from "./components/ScaleInput";
import { Preview } from "./components/Preview";
import { DxfViewer } from "./components/DxfViewer";
import { DxfDropZone } from "./components/DxfDropZone";
import { fetchPreview, fetchConvert, type PreviewResult, type CuttingParamsData } from "./api";
import CuttingParams from "./components/CuttingParams";

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
  const [outputFormat, setOutputFormat] = useState<"dxf" | "nc">("dxf");
  const [cuttingParams, setCuttingParams] = useState<CuttingParamsData>({});

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
      const blob = await fetchConvert(file, widthNum, heightNum, outputFormat, cuttingParams);
      const text = await blob.text();
      setDxfContent(text);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext = outputFormat === "nc" ? ".nc" : ".dxf";
      a.download = file.name.replace(/\.\w+$/, ext);
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    }
  }, [file, targetWidthMm, targetHeightMm, outputFormat, cuttingParams]);

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
              <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 8 }}>
                <span style={{ fontWeight: 500 }}>Output:</span>
                <label>
                  <input type="radio" name="format" value="dxf"
                    checked={outputFormat === "dxf"} onChange={() => setOutputFormat("dxf")} />
                  {" "}DXF
                </label>
                <label>
                  <input type="radio" name="format" value="nc"
                    checked={outputFormat === "nc"} onChange={() => setOutputFormat("nc")} />
                  {" "}NC (G-code)
                </label>
              </div>
              {outputFormat === "nc" && (
                <CuttingParams params={cuttingParams} onChange={setCuttingParams} />
              )}
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
                {outputFormat === "nc" ? "Download .nc" : "Download .dxf"}
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
