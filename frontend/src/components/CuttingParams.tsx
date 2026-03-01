import type { CuttingParamsData } from "../api";

interface Props {
  params: CuttingParamsData;
  onChange: (params: CuttingParamsData) => void;
}

const FIELDS: { key: keyof CuttingParamsData; label: string; default_: string; unit: string }[] = [
  { key: "feed_rate", label: "Feed Rate", default_: "3000", unit: "mm/min" },
  { key: "pierce_feed", label: "Pierce Feed", default_: "100", unit: "mm/min" },
  { key: "safe_z", label: "Safe Z", default_: "10", unit: "mm" },
  { key: "approach_z", label: "Approach Z", default_: "3", unit: "mm" },
  { key: "cut_z", label: "Cut Z", default_: "1.5", unit: "mm" },
  { key: "kerf_width", label: "Kerf Width", default_: "1.5", unit: "mm" },
  { key: "dwell", label: "Dwell", default_: "0.5", unit: "s" },
];

export default function CuttingParams({ params, onChange }: Props) {
  return (
    <div style={{ marginTop: 12 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 8,
        }}
      >
        {FIELDS.map(({ key, label, default_, unit }) => (
          <label key={key} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 14 }}>
            <span style={{ minWidth: 90 }}>{label}</span>
            <input
              type="number"
              min="0"
              step="any"
              placeholder={default_}
              value={params[key] ?? ""}
              onChange={(e) => onChange({ ...params, [key]: e.target.value })}
              style={{ width: 70, padding: 4 }}
            />
            <span style={{ color: "#888", fontSize: 12 }}>{unit}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
