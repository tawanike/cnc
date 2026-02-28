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
