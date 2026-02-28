import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.mark.asyncio
async def test_convert_endpoint(test_png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", test_png_bytes, "image/png")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/dxf"
    assert b"LWPOLYLINE" in response.content


@pytest.mark.asyncio
async def test_convert_with_scale(test_png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("test.png", test_png_bytes, "image/png")},
            data={"target_width_mm": "200"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_preview_endpoint(test_png_bytes):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/preview",
            files={"image": ("test.png", test_png_bytes, "image/png")},
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


@pytest.mark.asyncio
async def test_convert_invalid_image():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/convert",
            files={"image": ("bad.png", b"not an image", "image/png")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_convert_oversized_image():
    """Uploading a file larger than 20 MB should return 413."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        big_data = b"\x00" * (20 * 1024 * 1024 + 1)
        response = await client.post(
            "/api/convert",
            files={"image": ("big.png", big_data, "image/png")},
        )
    assert response.status_code == 413
