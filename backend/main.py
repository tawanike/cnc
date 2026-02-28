from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response

from backend.pipeline import convert_image, preview_image

app = FastAPI()


@app.post("/api/convert")
async def convert(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = await image.read()
    dxf_bytes = convert_image(
        image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
    )
    return Response(
        content=dxf_bytes,
        media_type="application/dxf",
        headers={"Content-Disposition": "attachment; filename=output.dxf"},
    )


@app.post("/api/preview")
async def preview(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
):
    image_bytes = await image.read()
    return preview_image(
        image_bytes, image.filename or "image.png", target_width_mm, target_height_mm
    )
