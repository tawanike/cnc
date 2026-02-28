import { type ChangeEvent } from "react";

interface ScaleInputProps {
  targetWidthMm: string;
  targetHeightMm: string;
  onWidthChange: (value: string) => void;
  onHeightChange: (value: string) => void;
}

export function ScaleInput({
  targetWidthMm,
  targetHeightMm,
  onWidthChange,
  onHeightChange,
}: ScaleInputProps) {
  return (
    <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 16 }}>
      <label>
        Width (mm):
        <input
          type="number"
          min="0"
          step="any"
          value={targetWidthMm}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            onWidthChange(e.target.value);
            onHeightChange("");
          }}
          placeholder="auto"
          style={{ marginLeft: 8, width: 100, padding: 4 }}
        />
      </label>
      <label>
        Height (mm):
        <input
          type="number"
          min="0"
          step="any"
          value={targetHeightMm}
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            onHeightChange(e.target.value);
            onWidthChange("");
          }}
          placeholder="auto"
          style={{ marginLeft: 8, width: 100, padding: 4 }}
        />
      </label>
    </div>
  );
}
