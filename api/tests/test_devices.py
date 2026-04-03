import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_device(client: AsyncClient, sample_device_payload: dict):
    resp = await client.post("/api/v1/devices", json=sample_device_payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == sample_device_payload["name"]
    assert data["device_type"] == "drilling_rig"
    assert data["status"] == "offline"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_create_device_duplicate_name(client: AsyncClient):
    payload = {"name": "Unique Rig", "device_type": "drilling_rig", "location": "Somewhere"}
    resp1 = await client.post("/api/v1/devices", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/devices", json=payload)
    assert resp2.status_code == 409


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, sample_device_payload: dict):
    await client.post("/api/v1/devices", json=sample_device_payload)
    resp = await client.get("/api/v1/devices")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_device(client: AsyncClient, sample_device_payload: dict):
    create_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/devices/{device_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == device_id


@pytest.mark.asyncio
async def test_get_device_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/devices/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_device_status_offline_when_no_telemetry(
    client: AsyncClient, sample_device_payload: dict
):
    resp = await client.post("/api/v1/devices", json=sample_device_payload)
    assert resp.json()["data"]["status"] == "offline"


@pytest.mark.asyncio
async def test_create_device_with_metadata(client: AsyncClient):
    payload = {
        "name": "Rig With Meta",
        "device_type": "drilling_rig",
        "location": "North Sea",
        "metadata": {"model": "HMH-500", "firmware": "3.2.1"},
    }
    resp = await client.post("/api/v1/devices", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["metadata"] == {"model": "HMH-500", "firmware": "3.2.1"}


@pytest.mark.asyncio
async def test_create_device_validation_error(client: AsyncClient):
    resp = await client.post(
        "/api/v1/devices", json={"name": "", "device_type": "", "location": ""}
    )
    assert resp.status_code == 422
