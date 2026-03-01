from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from backend.nc_writer import CuttingParams
from backend.pipeline import convert_image, preview_image

MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI()


@app.post("/api/convert")
def convert(
    image: UploadFile = File(...),
    target_width_mm: float | None = Form(None),
    target_height_mm: float | None = Form(None),
    format: str = Form("dxf"),
    feed_rate: float | None = Form(None),
    pierce_feed: float | None = Form(None),
    safe_z: float | None = Form(None),
    approach_z: float | None = Form(None),
    cut_z: float | None = Form(None),
    kerf_width: float | None = Form(None),
    dwell: float | None = Form(None),
):
    image_bytes = image.file.read()
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image too large (max 20 MB)")

    cutting_params: CuttingParams | None = None
    if format == "nc":
        param_overrides: dict[str, float] = {}
        for name, value in [
            ("feed_rate", feed_rate),
            ("pierce_feed", pierce_feed),
            ("safe_z", safe_z),
            ("approach_z", approach_z),
            ("cut_z", cut_z),
            ("kerf_width", kerf_width),
            ("dwell", dwell),
        ]:
            if value is not None:
                param_overrides[name] = value
        cutting_params = CuttingParams(**param_overrides)

    try:
        output_bytes = convert_image(
            image_bytes,
            image.filename or "image.png",
            target_width_mm,
            target_height_mm,
            output_format=format,
            cutting_params=cutting_params,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if format == "nc":
        return Response(
            content=output_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=output.nc"},
        )
    return Response(
        content=output_bytes,
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
