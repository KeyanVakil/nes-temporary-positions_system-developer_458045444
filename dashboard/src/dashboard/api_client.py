import os

import httpx

API_BASE = os.environ.get("DASHBOARD_API_BASE_URL", "http://api:8000")


def _url(path: str) -> str:
    return f"{API_BASE}/api/v1{path}"


def get_devices() -> list[dict]:
    resp = httpx.get(_url("/devices"), timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_device(device_id: str) -> dict:
    resp = httpx.get(_url(f"/devices/{device_id}"), timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_telemetry(device_id: str, limit: int = 300) -> list[dict]:
    resp = httpx.get(_url(f"/telemetry/{device_id}"), params={"limit": limit}, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_latest_telemetry(device_id: str) -> dict | None:
    resp = httpx.get(_url(f"/telemetry/{device_id}/latest"), timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_alerts(device_id: str | None = None, acknowledged: bool | None = None, limit: int = 50) -> list[dict]:
    params: dict = {"limit": limit}
    if device_id:
        params["device_id"] = device_id
    if acknowledged is not None:
        params["acknowledged"] = str(acknowledged).lower()
    resp = httpx.get(_url("/alerts"), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def acknowledge_alert(alert_id: str) -> dict:
    resp = httpx.patch(_url(f"/alerts/{alert_id}/acknowledge"), timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]


def get_stats() -> dict:
    resp = httpx.get(_url("/stats"), timeout=10)
    resp.raise_for_status()
    return resp.json()["data"]
