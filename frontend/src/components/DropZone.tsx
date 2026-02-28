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
