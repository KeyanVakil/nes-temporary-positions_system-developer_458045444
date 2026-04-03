import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_telemetry(
    client: AsyncClient, sample_device_payload: dict, sample_telemetry_reading: dict
):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    payload = {"device_id": device_id, "readings": [sample_telemetry_reading]}
    resp = await client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["ingested"] == 1


@pytest.mark.asyncio
async def test_ingest_telemetry_invalid_device(client: AsyncClient, sample_telemetry_reading: dict):
    payload = {
        "device_id": "00000000-0000-0000-0000-000000000000",
        "readings": [sample_telemetry_reading],
    }
    resp = await client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_ingest_telemetry_invalid_values(client: AsyncClient, sample_device_payload: dict):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    bad_reading = {
        "timestamp": "2026-04-03T12:00:00Z",
        "rpm": 999.0,  # exceeds max 300
        "wob": 35.0,
        "torque": 22.0,
        "mud_flow_rate": 2800.0,
        "vibration": 3.5,
    }
    payload = {"device_id": device_id, "readings": [bad_reading]}
    resp = await client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_telemetry_history(
    client: AsyncClient, sample_device_payload: dict, sample_telemetry_reading: dict
):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    # Ingest multiple readings
    for _ in range(3):
        payload = {"device_id": device_id, "readings": [sample_telemetry_reading]}
        await client.post("/api/v1/telemetry", json=payload)

    resp = await client.get(f"/api/v1/telemetry/{device_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 3


@pytest.mark.asyncio
async def test_get_latest_telemetry(
    client: AsyncClient, sample_device_payload: dict, sample_telemetry_reading: dict
):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    payload = {"device_id": device_id, "readings": [sample_telemetry_reading]}
    await client.post("/api/v1/telemetry", json=payload)

    resp = await client.get(f"/api/v1/telemetry/{device_id}/latest")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["rpm"] == 120.0


@pytest.mark.asyncio
async def test_get_latest_telemetry_none(client: AsyncClient, sample_device_payload: dict):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    resp = await client.get(f"/api/v1/telemetry/{device_id}/latest")
    assert resp.status_code == 200
    assert resp.json()["data"] is None


@pytest.mark.asyncio
async def test_get_telemetry_device_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/telemetry/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_telemetry_pagination(
    client: AsyncClient, sample_device_payload: dict, sample_telemetry_reading: dict
):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    for _ in range(5):
        await client.post(
            "/api/v1/telemetry",
            json={"device_id": device_id, "readings": [sample_telemetry_reading]},
        )

    resp = await client.get(f"/api/v1/telemetry/{device_id}", params={"limit": 2})
    assert len(resp.json()["data"]) == 2


@pytest.mark.asyncio
async def test_ingest_batch_readings(
    client: AsyncClient, sample_device_payload: dict, sample_telemetry_reading: dict
):
    dev_resp = await client.post("/api/v1/devices", json=sample_device_payload)
    device_id = dev_resp.json()["data"]["id"]

    payload = {
        "device_id": device_id,
        "readings": [sample_telemetry_reading, sample_telemetry_reading],
    }
    resp = await client.post("/api/v1/telemetry", json=payload)
    assert resp.status_code == 201
    assert resp.json()["data"]["ingested"] == 2
