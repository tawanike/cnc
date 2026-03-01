// frontend/src/App.tsx
import { useState, useEffect, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { ImageCropper } from "./components/ImageCropper";
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
  const [croppedFile, setCroppedFile] = useState<File | null>(null);
  const [showCropper, setShowCropper] = useState(false);
  const [imageUrl, setImageUrl] = useState<string | null>(null);

  // Viewer state
  const [viewerDxf, setViewerDxf] = useState<string | null>(null);
  const [viewerFilename, setViewerFilename] = useState<string | null>(null);

  const handleFileSelect = useCallback((f: File) => {
    setFile(f);
    setCroppedFile(null);
    setShowCropper(true);
    setImageUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(f); });
  }, []);

  const handleCropApply = useCallback((cropped: File) => {
    setCroppedFile(cropped);
    setShowCropper(false);
  }, []);

  const handleCropSkip = useCallback(() => {
    setShowCropper(false);
  }, []);

  const handleCropReset = useCallback(() => {
    setCroppedFile(null);
    setShowCropper(true);
  }, []);

  useEffect(() => {
    const activeFile = croppedFile ?? file;
    if (!activeFile || showCropper) return;
    setDxfContent(null);
    const timeoutId = setTimeout(() => {
      setLoading(true);
      setError(null);
      const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
      const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
      fetchPreview(activeFile, widthNum, heightNum)
        .then(setPreviewData)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 400);
    return () => clearTimeout(timeoutId);
  }, [file, croppedFile, showCropper, targetWidthMm, targetHeightMm]);

  const handleDownload = useCallback(async () => {
    const activeFile = croppedFile ?? file;
    if (!activeFile) return;
    setError(null);
    const widthNum = targetWidthMm ? parseFloat(targetWidthMm) : undefined;
    const heightNum = targetHeightMm ? parseFloat(targetHeightMm) : undefined;
    try {
      const blob = await fetchConvert(activeFile, widthNum, heightNum, outputFormat, cuttingParams);
      const text = await blob.text();
      setDxfContent(text);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext = outputFormat === "nc" ? ".nc" : ".dxf";
      const baseName = file?.name.replace(/\.\w+$/, "") ?? "output";
      a.download = baseName + ext;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    }
  }, [file, croppedFile, targetWidthMm, targetHeightMm, outputFormat, cuttingParams]);

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
          <DropZone onFileSelect={handleFileSelect} />
          {file && showCropper && imageUrl && (
            <ImageCropper
              imageUrl={imageUrl}
              onCropApply={handleCropApply}
              onSkip={handleCropSkip}
            />
          )}
          {file && !showCropper && (
            <>
              <button
                onClick={handleCropReset}
                style={{
                  marginTop: 8,
                  padding: "4px 12px",
                  fontSize: 13,
                  background: "white",
                  color: "#6b7280",
                  border: "1px solid #d1d5db",
                  borderRadius: 4,
                  cursor: "pointer",
                }}
              >
                Re-crop Image
              </button>
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
