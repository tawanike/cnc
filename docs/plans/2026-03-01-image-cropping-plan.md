# Image Cropping Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a client-side image cropping step after upload so users can isolate the exact region they need before conversion.

**Architecture:** New `ImageCropper.tsx` component using `react-image-crop` renders after image upload. User draws a crop rectangle (with optional aspect ratio lock), clicks "Apply Crop", and a Canvas-extracted PNG replaces the original file for preview/convert. No backend changes.

**Tech Stack:** react-image-crop, Canvas API, React 19

---

### Task 1: Install react-image-crop

**Files:**
- Modify: `frontend/package.json`

**Step 1: Install the dependency**

Run from `frontend/` directory:
```bash
cd frontend && npm install react-image-crop
```

**Step 2: Verify installation**

Run: `cd frontend && npm ls react-image-crop`
Expected: `react-image-crop@<version>` listed

**Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "feat: add react-image-crop dependency"
```

---

### Task 2: Create ImageCropper component

**Files:**
- Create: `frontend/src/components/ImageCropper.tsx`

**Step 1: Create the component**

```tsx
import { useState, useRef, useCallback } from "react";
import ReactCrop, { type Crop, type PixelCrop } from "react-image-crop";
import "react-image-crop/dist/ReactCrop.css";

interface ImageCropperProps {
  imageUrl: string;
  onCropApply: (croppedFile: File) => void;
  onSkip: () => void;
}

type AspectOption = "free" | "1:1" | "4:3" | "16:9" | "custom";

const ASPECT_RATIOS: Record<string, number | undefined> = {
  free: undefined,
  "1:1": 1,
  "4:3": 4 / 3,
  "16:9": 16 / 9,
};

export function ImageCropper({ imageUrl, onCropApply, onSkip }: ImageCropperProps) {
  const imgRef = useRef<HTMLImageElement | null>(null);
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const [aspectOption, setAspectOption] = useState<AspectOption>("free");
  const [customW, setCustomW] = useState("4");
  const [customH, setCustomH] = useState("3");

  const aspect =
    aspectOption === "custom"
      ? (parseFloat(customW) || 1) / (parseFloat(customH) || 1)
      : ASPECT_RATIOS[aspectOption];

  const handleApply = useCallback(async () => {
    const image = imgRef.current;
    if (!image || !completedCrop) return;

    const canvas = document.createElement("canvas");
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;
    canvas.width = completedCrop.width * scaleX;
    canvas.height = completedCrop.height * scaleY;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(
      image,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height,
    );

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, "image/png"),
    );
    if (!blob) return;

    const file = new File([blob], "cropped.png", { type: "image/png" });
    onCropApply(file);
  }, [completedCrop, onCropApply]);

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
        <span style={{ fontWeight: 500 }}>Aspect:</span>
        {(["free", "1:1", "4:3", "16:9", "custom"] as AspectOption[]).map((opt) => (
          <button
            key={opt}
            onClick={() => { setAspectOption(opt); setCrop(undefined); }}
            style={{
              padding: "4px 12px",
              border: aspectOption === opt ? "2px solid #2563eb" : "1px solid #d1d5db",
              borderRadius: 4,
              background: aspectOption === opt ? "#eff6ff" : "white",
              cursor: "pointer",
              fontWeight: aspectOption === opt ? 600 : 400,
            }}
          >
            {opt === "free" ? "Free" : opt === "custom" ? "Custom" : opt}
          </button>
        ))}
        {aspectOption === "custom" && (
          <>
            <input
              type="number"
              value={customW}
              onChange={(e) => { setCustomW(e.target.value); setCrop(undefined); }}
              style={{ width: 50, padding: "4px 6px", border: "1px solid #d1d5db", borderRadius: 4 }}
              min="1"
            />
            <span>:</span>
            <input
              type="number"
              value={customH}
              onChange={(e) => { setCustomH(e.target.value); setCrop(undefined); }}
              style={{ width: 50, padding: "4px 6px", border: "1px solid #d1d5db", borderRadius: 4 }}
              min="1"
            />
          </>
        )}
      </div>

      <ReactCrop
        crop={crop}
        onChange={(c) => setCrop(c)}
        onComplete={(c) => setCompletedCrop(c)}
        aspect={aspect}
      >
        <img
          ref={imgRef}
          src={imageUrl}
          alt="Crop source"
          style={{ maxWidth: "100%", maxHeight: 600 }}
          crossOrigin="anonymous"
        />
      </ReactCrop>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button
          onClick={handleApply}
          disabled={!completedCrop}
          style={{
            padding: "8px 20px",
            background: completedCrop ? "#2563eb" : "#d1d5db",
            color: "white",
            border: "none",
            borderRadius: 6,
            cursor: completedCrop ? "pointer" : "not-allowed",
            fontWeight: 500,
          }}
        >
          Apply Crop
        </button>
        <button
          onClick={onSkip}
          style={{
            padding: "8px 20px",
            background: "white",
            color: "#6b7280",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          Skip Cropping
        </button>
      </div>
    </div>
  );
}
```

**Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/components/ImageCropper.tsx
git commit -m "feat: ImageCropper component with aspect ratio support"
```

---

### Task 3: Integrate ImageCropper into App.tsx

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Add cropper state and integrate component**

Changes to `App.tsx`:

1. Add import at top:
```tsx
import { ImageCropper } from "./components/ImageCropper";
```

2. Add new state variables after the existing state declarations (after line 25):
```tsx
const [croppedFile, setCroppedFile] = useState<File | null>(null);
const [showCropper, setShowCropper] = useState(false);
const [imageUrl, setImageUrl] = useState<string | null>(null);
```

3. Add a handler for when a file is selected. Replace `<DropZone onFileSelect={setFile} />` with:
```tsx
<DropZone onFileSelect={(f) => {
  setFile(f);
  setCroppedFile(null);
  setShowCropper(true);
  setImageUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(f); });
}} />
```

4. Add crop handlers:
```tsx
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
```

5. Change the `useEffect` for preview (line 31-45) to use `croppedFile ?? file` instead of `file`:
```tsx
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
```

6. Change `handleDownload` to use `croppedFile ?? file`:
```tsx
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
```

7. In the JSX, after `<DropZone>` and inside the `{file && ...}` block, add the cropper and reset button. The converter section should be:
```tsx
{tab === "converter" && (
  <>
    <DropZone onFileSelect={(f) => {
      setFile(f);
      setCroppedFile(null);
      setShowCropper(true);
      setImageUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return URL.createObjectURL(f); });
    }} />
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
```

**Step 2: Verify it compiles**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

**Step 3: Build to verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: integrate ImageCropper into converter workflow"
```

---

### Task 4: Build and verify end-to-end

**Files:**
- None (verification only)

**Step 1: Build frontend**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 2: Run backend tests**

Run: `cd /home/tawanda/dev/amengineering/cnc && source venv/bin/activate && pytest -v`
Expected: All tests pass (no backend changes, so existing tests should be green)

**Step 3: Commit and push**

```bash
git add -A
git commit -m "feat: image cropping tool with aspect ratio support"
```
