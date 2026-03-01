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


@pytest.mark.asyncio
async def test_convert_nc_format(test_png_bytes):
    """POST /api/convert with format=nc should return NC file."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/convert",
            files={"image": ("test.png", test_png_bytes, "image/png")},
            data={"format": "nc"},
        )
    assert resp.status_code == 200
    assert "output.nc" in resp.headers["content-disposition"]
    assert "G21" in resp.text


@pytest.mark.asyncio
async def test_convert_nc_with_params(test_png_bytes):
    """NC endpoint should accept cutting parameters."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/convert",
            files={"image": ("test.png", test_png_bytes, "image/png")},
            data={
                "format": "nc",
                "feed_rate": "2000",
                "safe_z": "15",
            },
        )
    assert resp.status_code == 200
    assert "F2000" in resp.text
    assert "Z15.0000" in resp.text


@pytest.mark.asyncio
async def test_convert_default_still_dxf(test_png_bytes):
    """Default format should remain DXF."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/convert",
            files={"image": ("test.png", test_png_bytes, "image/png")},
        )
    assert resp.status_code == 200
    assert "output.dxf" in resp.headers["content-disposition"]
