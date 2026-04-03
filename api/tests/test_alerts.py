import pytest
from httpx import AsyncClient

from drillsense.services.alert_service import OPERATOR_MAP

# --- Unit tests for alert threshold logic ---


class TestOperatorMap:
    def test_gt(self):
        assert OPERATOR_MAP["gt"](10, 5) is True
        assert OPERATOR_MAP["gt"](5, 10) is False
        assert OPERATOR_MAP["gt"](5, 5) is False

    def test_lt(self):
        assert OPERATOR_MAP["lt"](3, 5) is True
        assert OPERATOR_MAP["lt"](5, 3) is False
        assert OPERATOR_MAP["lt"](5, 5) is False

    def test_gte(self):
        assert OPERATOR_MAP["gte"](5, 5) is True
        assert OPERATOR_MAP["gte"](6, 5) is True
        assert OPERATOR_MAP["gte"](4, 5) is False

    def test_lte(self):
        assert OPERATOR_MAP["lte"](5, 5) is True
        assert OPERATOR_MAP["lte"](4, 5) is True
        assert OPERATOR_MAP["lte"](6, 5) is False


# --- Integration tests ---


@pytest.mark.asyncio
async def test_create_alert_rule(client: AsyncClient):
    payload = {
        "name": "Test High Vibration",
        "metric": "vibration",
        "operator": "gt",
        "threshold_value": 8.0,
        "severity": "high",
        "device_type": "drilling_rig",
    }
    resp = await client.post("/api/v1/alerts/rules", json=payload)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Test High Vibration"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_alert_rule_invalid_metric(client: AsyncClient):
    payload = {
        "name": "Bad Rule",
        "metric": "invalid_metric",
        "operator": "gt",
        "threshold_value": 5.0,
        "severity": "low",
    }
    resp = await client.post("/api/v1/alerts/rules", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_rule_invalid_operator(client: AsyncClient):
    payload = {
        "name": "Bad Rule",
        "metric": "rpm",
        "operator": "eq",
        "threshold_value": 5.0,
        "severity": "low",
    }
    resp = await client.post("/api/v1/alerts/rules", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_alert_rules(client: AsyncClient):
    payload = {
        "name": "List Test Rule",
        "metric": "rpm",
        "operator": "gt",
        "threshold_value": 200.0,
        "severity": "medium",
    }
    await client.post("/api/v1/alerts/rules", json=payload)
    resp = await client.get("/api/v1/alerts/rules")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_alert_triggered_by_threshold_breach(client: AsyncClient):
    # Create rule: vibration > 8.0
    rule_payload = {
        "name": "Vib Alert",
        "metric": "vibration",
        "operator": "gt",
        "threshold_value": 8.0,
        "severity": "high",
    }
    await client.post("/api/v1/alerts/rules", json=rule_payload)

    # Create device
    dev_resp = await client.post(
        "/api/v1/devices",
        json={"name": "Alert Test Rig", "device_type": "drilling_rig", "location": "Test"},
    )
    device_id = dev_resp.json()["data"]["id"]

    # Send telemetry that breaches threshold
    reading = {
        "timestamp": "2026-04-03T12:00:00Z",
        "rpm": 100.0,
        "wob": 30.0,
        "torque": 20.0,
        "mud_flow_rate": 2500.0,
        "vibration": 12.0,  # > 8.0 threshold
    }
    await client.post("/api/v1/telemetry", json={"device_id": device_id, "readings": [reading]})

    # Check alerts
    resp = await client.get("/api/v1/alerts", params={"device_id": device_id})
    assert resp.status_code == 200
    alerts = resp.json()["data"]
    assert len(alerts) >= 1
    assert alerts[0]["metric"] == "vibration"
    assert alerts[0]["actual_value"] == 12.0
    assert alerts[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_no_alert_when_within_threshold(client: AsyncClient):
    rule_payload = {
        "name": "No Alert Rule",
        "metric": "vibration",
        "operator": "gt",
        "threshold_value": 8.0,
        "severity": "high",
    }
    await client.post("/api/v1/alerts/rules", json=rule_payload)

    dev_resp = await client.post(
        "/api/v1/devices",
        json={"name": "Normal Rig", "device_type": "drilling_rig", "location": "Test"},
    )
    device_id = dev_resp.json()["data"]["id"]

    reading = {
        "timestamp": "2026-04-03T12:00:00Z",
        "rpm": 100.0,
        "wob": 30.0,
        "torque": 20.0,
        "mud_flow_rate": 2500.0,
        "vibration": 3.0,  # well within threshold
    }
    await client.post("/api/v1/telemetry", json={"device_id": device_id, "readings": [reading]})

    resp = await client.get("/api/v1/alerts", params={"device_id": device_id})
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_acknowledge_alert(client: AsyncClient):
    # Create rule and trigger alert
    await client.post(
        "/api/v1/alerts/rules",
        json={
            "name": "Ack Test",
            "metric": "vibration",
            "operator": "gt",
            "threshold_value": 8.0,
            "severity": "high",
        },
    )
    dev_resp = await client.post(
        "/api/v1/devices",
        json={"name": "Ack Test Rig", "device_type": "drilling_rig", "location": "Test"},
    )
    device_id = dev_resp.json()["data"]["id"]

    reading = {
        "timestamp": "2026-04-03T12:00:00Z",
        "rpm": 100.0,
        "wob": 30.0,
        "torque": 20.0,
        "mud_flow_rate": 2500.0,
        "vibration": 15.0,
    }
    await client.post("/api/v1/telemetry", json={"device_id": device_id, "readings": [reading]})

    alerts_resp = await client.get("/api/v1/alerts", params={"device_id": device_id})
    alert_id = alerts_resp.json()["data"][0]["id"]

    # Acknowledge
    ack_resp = await client.patch(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["data"]["acknowledged"] is True
    assert ack_resp.json()["data"]["acknowledged_at"] is not None


@pytest.mark.asyncio
async def test_acknowledge_nonexistent_alert(client: AsyncClient):
    resp = await client.patch("/api/v1/alerts/00000000-0000-0000-0000-000000000000/acknowledge")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_filter_alerts_by_severity(client: AsyncClient):
    # Create two rules with different severities
    await client.post(
        "/api/v1/alerts/rules",
        json={
            "name": "High Vib",
            "metric": "vibration",
            "operator": "gt",
            "threshold_value": 8.0,
            "severity": "high",
        },
    )
    await client.post(
        "/api/v1/alerts/rules",
        json={
            "name": "Crit Vib",
            "metric": "vibration",
            "operator": "gt",
            "threshold_value": 12.0,
            "severity": "critical",
        },
    )

    dev_resp = await client.post(
        "/api/v1/devices",
        json={"name": "Filter Test Rig", "device_type": "drilling_rig", "location": "Test"},
    )
    device_id = dev_resp.json()["data"]["id"]

    reading = {
        "timestamp": "2026-04-03T12:00:00Z",
        "rpm": 100.0,
        "wob": 30.0,
        "torque": 20.0,
        "mud_flow_rate": 2500.0,
        "vibration": 15.0,
    }
    await client.post("/api/v1/telemetry", json={"device_id": device_id, "readings": [reading]})

    # Filter by severity
    resp = await client.get("/api/v1/alerts", params={"severity": "critical"})
    assert resp.status_code == 200
    for alert in resp.json()["data"]:
        assert alert["severity"] == "critical"
