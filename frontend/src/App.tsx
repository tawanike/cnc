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
