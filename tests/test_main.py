import io
import numpy as np
from PIL import Image
import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


def _make_test_png() -> bytes:
    img = np.ones((100, 100), dtype=np.uint8) * 255
    img[20:80, 20:80] = 0
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_convert_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png, "image/png")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert b"LWPOLYLINE" in response.content


@pytest.mark.asyncio
async def test_convert_with_scale():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", png, "image/png")},
            data={"target_width_mm": "200"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_preview_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        png = _make_test_png()
        response = await client.post(
            "/api/preview",
            files={"image": ("test.png", png, "image/png")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "svg" in data
    assert "<svg" in data["svg"]
    assert "stats" in data
    assert data["stats"]["path_count"] > 0


@pytest.mark.asyncio
async def test_convert_no_file():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/convert")
    assert response.status_code == 422
