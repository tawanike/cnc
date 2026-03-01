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
