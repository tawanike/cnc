# Image Cropping Tool Design

## Goal

Add a client-side image cropping step so users can isolate the exact part of an uploaded image before conversion to DXF or NC.

## Context

Currently, the entire uploaded image is converted. Users working with photos of sheets or multi-part drawings need to isolate a specific region before tracing. Cropping should happen after upload but before the scale/format/convert step.

## Architecture

No backend changes. Cropping is entirely client-side using `react-image-crop`. The cropped image is a standard PNG blob sent to the existing `/api/convert` and `/api/preview` endpoints.

```
Upload → Crop (new) → Scale → Preview → Convert → Download
```

## New Component: `ImageCropper.tsx`

Uses `react-image-crop` library to render a draggable, resizable crop rectangle over the uploaded image.

Features:
- Drag-to-select crop rectangle with resize handles
- Aspect ratio selector: Free, 1:1, 4:3, 16:9, Custom (two number inputs)
- "Apply Crop" button extracts the cropped region via Canvas API and produces a new File/Blob
- Callback to parent with the cropped file

Canvas extraction flow:
1. Draw the cropped region of the source image onto an offscreen canvas
2. Export the canvas as a PNG blob
3. Wrap in a File object to match the existing API contract

## App.tsx Changes

New state:
- `croppedFile: File | null` — the file sent to preview/convert (replaces `file` when crop is applied)
- `showCropper: boolean` — controls crop UI visibility

Flow:
1. User uploads image → `showCropper = true`, crop UI appears
2. User adjusts crop region and aspect ratio
3. "Apply Crop" → `croppedFile` set, cropper hides, preview auto-triggers with cropped image
4. "Reset Crop" → clears `croppedFile`, re-shows cropper with original image
5. Preview and convert always use `croppedFile ?? file`

## Aspect Ratio Options

| Option | Ratio | Description |
|--------|-------|-------------|
| Free | none | No constraint, freeform rectangle |
| 1:1 | 1 | Square crop |
| 4:3 | 4/3 | Standard photo ratio |
| 16:9 | 16/9 | Widescreen ratio |
| Custom | user input | Two number fields for arbitrary ratio |

## Dependencies

- Add `react-image-crop` (~8KB) — mature, purpose-built React cropping library

## API Changes

None. The server receives a normal image file.
