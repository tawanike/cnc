from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from backend.pipeline import convert_image, preview_image

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI()


@app.post("/api/convert")
def convert(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = image.file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large (max 20 MB)")
    try:
        dxf_bytes = convert_image(
            image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": "attachment; filename=output.dxf"},
    )


@app.post("/api/preview")
def preview(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = image.file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large (max 20 MB)")
    try:
        return preview_image(
            image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Serve frontend build if it exists (production)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
