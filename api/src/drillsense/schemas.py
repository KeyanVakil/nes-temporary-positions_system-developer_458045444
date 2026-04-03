import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

# --- Response envelope ---


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    count: int | None = None


class Envelope(BaseModel):
    data: Any
    meta: Meta = Field(default_factory=Meta)


# --- Device schemas ---


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    device_type: str = Field(..., min_length=1, max_length=100)
    location: str = Field(..., min_length=1, max_length=255)
    metadata: dict | None = None


class DeviceResponse(BaseModel):
    id: uuid.UUID
    name: str
    device_type: str
    location: str
    metadata: dict | None = None
    status: str  # online, offline, alert
    created_at: datetime
    last_seen_at: datetime | None = None

    model_config = {"from_attributes": True}


# --- Telemetry schemas ---

TELEMETRY_RANGES: dict[str, tuple[float, float]] = {
    "rpm": (0.0, 300.0),
    "wob": (0.0, 100.0),
    "torque": (0.0, 100.0),
    "mud_flow_rate": (0.0, 5000.0),
    "vibration": (0.0, 20.0),
}


class TelemetryValue(BaseModel):
    timestamp: datetime
    rpm: float = Field(..., ge=0.0, le=300.0)
    wob: float = Field(..., ge=0.0, le=100.0)
    torque: float = Field(..., ge=0.0, le=100.0)
    mud_flow_rate: float = Field(..., ge=0.0, le=5000.0)
    vibration: float = Field(..., ge=0.0, le=20.0)


class TelemetryIngest(BaseModel):
    device_id: uuid.UUID
    readings: list[TelemetryValue] = Field(..., min_length=1)


class TelemetryResponse(BaseModel):
    id: int
    device_id: uuid.UUID
    timestamp: datetime
    rpm: float
    wob: float
    torque: float
    mud_flow_rate: float
    vibration: float

    model_config = {"from_attributes": True}


# --- Alert schemas ---

VALID_METRICS = {"rpm", "wob", "torque", "mud_flow_rate", "vibration"}
VALID_OPERATORS = {"gt", "lt", "gte", "lte"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}


class AlertRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    metric: str
    operator: str
    threshold_value: float
    severity: str
    device_type: str | None = None

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        if v not in VALID_METRICS:
            raise ValueError(f"metric must be one of {VALID_METRICS}")
        return v

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        if v not in VALID_OPERATORS:
            raise ValueError(f"operator must be one of {VALID_OPERATORS}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        return v


class AlertRuleResponse(BaseModel):
    id: uuid.UUID
    name: str
    metric: str
    operator: str
    threshold_value: float
    severity: str
    device_type: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    rule_id: uuid.UUID
    metric: str
    threshold_value: float
    actual_value: float
    severity: str
    message: str | None = None
    acknowledged: bool
    acknowledged_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Health schemas ---


class HealthResponse(BaseModel):
    status: str
    database: str
    uptime_seconds: float


class StatsResponse(BaseModel):
    total_devices: int
    online_devices: int
    total_readings: int
    active_alerts: int
