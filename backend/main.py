from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.pipeline import convert_image, preview_image

app = FastAPI()


@app.post("/api/convert")
def convert(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = image.file.read()
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
    try:
        return preview_image(
            image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
