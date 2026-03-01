export interface PreviewResult {
  svg: string;
  stats: {
    path_count: number;
    point_count: number;
    width_mm: number;
    height_mm: number;
  };
}

export async function fetchPreview(
  file: File,
  targetWidthMm?: number,
  targetHeightMm?: number
): Promise<PreviewResult> {
  const form = new FormData();
  form.append("image", file);
  if (targetWidthMm) form.append("target_width_mm", String(targetWidthMm));
  if (targetHeightMm) form.append("target_height_mm", String(targetHeightMm));

  const res = await fetch("/api/preview", { method: "POST", body: form });
  if (!res.ok) throw new Error(`Preview failed: ${res.status}`);
  return res.json();
}

export interface CuttingParamsData {
  feed_rate?: string;
  pierce_feed?: string;
  safe_z?: string;
  approach_z?: string;
  cut_z?: string;
  kerf_width?: string;
  dwell?: string;
}

export async function fetchConvert(
  file: File,
  targetWidthMm?: number,
  targetHeightMm?: number,
  format: string = "dxf",
  cuttingParams?: CuttingParamsData,
): Promise<Blob> {
  const form = new FormData();
  form.append("image", file);
  form.append("format", format);
  if (targetWidthMm) form.append("target_width_mm", String(targetWidthMm));
  if (targetHeightMm) form.append("target_height_mm", String(targetHeightMm));
  if (format === "nc" && cuttingParams) {
    for (const [key, value] of Object.entries(cuttingParams)) {
      if (value) form.append(key, value);
    }
  }

  const res = await fetch("/api/convert", { method: "POST", body: form });
  if (!res.ok) throw new Error(`Convert failed: ${res.status}`);
  return res.blob();
}
