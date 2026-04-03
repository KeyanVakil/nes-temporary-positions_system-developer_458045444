# Product Requirements Document: DrillSense — Industrial Equipment Telemetry Platform

## 1. Project Overview

### What It Does
DrillSense is a backend-focused industrial IoT platform that ingests, processes, stores, and visualizes telemetry data from drilling equipment sensors. It simulates a realistic subset of HMH's domain — monitoring drilling parameters like rotary speed (RPM), weight on bit (WOB), torque, mud flow rate, and vibration levels from multiple rigs.

### Why It's Relevant
HMH builds and services drilling equipment globally. A core part of their digital strategy involves secure data platforms and IoT systems that connect equipment in the field to cloud-based monitoring and analytics. This project demonstrates exactly the kind of system a System Developer at HMH would build and maintain:

- **Backend services** that ingest high-frequency sensor data via REST APIs
- **Integration layer** connecting simulated IoT devices to a central data platform
- **Secure, containerized architecture** ready for cloud deployment
- **Production-grade engineering practices** — CI/CD, automated testing, code quality

### The Problem It Solves
Drilling operations generate massive amounts of sensor data. Operators need real-time visibility into equipment health, early warnings for anomalous conditions (e.g., excessive vibration indicating equipment wear), and historical trend analysis to plan maintenance. DrillSense provides this through a clean API layer and a monitoring dashboard.

---

## 2. Technical Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose Network                   │
│                                                              │
│  ┌──────────────┐     ┌──────────────────┐                  │
│  │  IoT Device   │────▶│   Ingestion API   │                 │
│  │  Simulator    │ HTTP│   (FastAPI)        │                 │
│  │  (Python)     │     │                    │                 │
│  └──────────────┘     │  POST /telemetry   │                 │
│                        │  POST /devices     │                 │
│                        │  GET  /alerts      │                 │
│                        └────────┬───────────┘                │
│                                 │                             │
│                        ┌────────▼───────────┐                │
│                        │   PostgreSQL        │                │
│                        │   (Time-series      │                │
│                        │    + device registry)│               │
│                        └────────┬───────────┘                │
│                                 │                             │
│                        ┌────────▼───────────┐                │
│                        │   Alert Engine      │                │
│                        │   (Background task) │                │
│                        │   Threshold checks  │                │
│                        └────────┬───────────┘                │
│                                 │                             │
│                        ┌────────▼───────────┐                │
│                        │   Web Dashboard     │                │
│                        │   (Streamlit)       │                │
│                        └────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility |
|-----------|---------------|
| **Ingestion API** (FastAPI) | REST API for device registration, telemetry ingestion, alert queries, and data retrieval. Core backend service. |
| **IoT Device Simulator** | Generates realistic drilling sensor data (RPM, WOB, torque, mud flow, vibration) with configurable anomaly injection. Simulates multiple rigs posting via HTTP. |
| **Alert Engine** | Background process within the API service. Evaluates incoming telemetry against configurable thresholds and generates alerts (e.g., vibration exceeding safe limits). |
| **PostgreSQL** | Stores device registry, telemetry readings (time-series), alert thresholds, and alert history. |
| **Web Dashboard** (Streamlit) | Displays real-time equipment status, telemetry charts, active alerts, and device health overview. Read-only consumer of the API. |

### Data Flow

1. **Simulator** generates sensor readings for N rigs at configurable intervals (default: every 2 seconds)
2. Each reading is **POST**ed to the Ingestion API as a JSON payload
3. The API **validates** the payload, **stores** it in PostgreSQL, and **evaluates** alert rules
4. If a threshold is breached, an **alert record** is created with severity and context
5. The **Dashboard** polls the API for latest telemetry and active alerts, rendering charts and status indicators

---

## 3. Tech Stack

| Technology | Role | Rationale |
|-----------|------|-----------|
| **Python 3.12** | Primary language | Industry-standard for backend services and IoT platforms. Fast development cycle. |
| **FastAPI** | REST API framework | Async-capable, automatic OpenAPI docs, Pydantic validation — ideal for API-first development. |
| **PostgreSQL 16** | Database | Robust relational DB with excellent time-series query support via native window functions and indexing. Production-grade. |
| **SQLAlchemy 2.x** | ORM / DB access | Type-safe database access, migration support via Alembic. |
| **Alembic** | DB migrations | Versioned schema migrations — standard DevOps practice. |
| **Streamlit** | Web dashboard | Rapid data-app development for monitoring UIs. No frontend framework needed for this backend-focused role. |
| **Docker + Docker Compose** | Containerization | All services containerized. Single `docker compose up` to run everything. |
| **pytest** | Testing framework | Unit and integration tests with fixtures, parameterization, and coverage reporting. |
| **GitHub Actions** | CI/CD | Automated lint, test, build pipeline on every push. Demonstrates CI/CD practices. |
| **Ruff** | Linting/formatting | Fast Python linter and formatter — enforces code quality standards. |
| **httpx** | HTTP client | Async HTTP client used by the simulator and in integration tests. |

---

## 4. Features & Acceptance Criteria

### Feature 1: Device Registration & Management API

Devices (drilling rigs) must be registered before sending telemetry.

**Acceptance Criteria:**
- `POST /api/v1/devices` creates a new device with name, location, and type
- `GET /api/v1/devices` lists all registered devices with their last-seen timestamp
- `GET /api/v1/devices/{device_id}` returns device details including current status (online/offline/alert)
- A device is marked "offline" if no telemetry received in the last 60 seconds
- Duplicate device names return `409 Conflict`
- All endpoints return proper HTTP status codes and JSON error bodies

### Feature 2: Telemetry Ingestion API

High-frequency sensor data ingestion with validation.

**Acceptance Criteria:**
- `POST /api/v1/telemetry` accepts a batch of sensor readings for a device
- Payload is validated: all values must be within physically plausible ranges (e.g., RPM 0-300, WOB 0-100 klbs)
- Invalid device IDs return `404`; invalid values return `422` with field-level errors
- Readings are stored with microsecond-precision timestamps
- `GET /api/v1/telemetry/{device_id}?start=...&end=...&limit=...` retrieves historical readings with pagination
- `GET /api/v1/telemetry/{device_id}/latest` returns the most recent reading

### Feature 3: Alert Engine with Configurable Thresholds

Automated anomaly detection based on threshold rules.

**Acceptance Criteria:**
- `POST /api/v1/alerts/rules` creates a threshold rule (e.g., "vibration > 8.0 g for device type X → severity HIGH")
- `GET /api/v1/alerts` lists active alerts, filterable by device, severity, and time range
- `PATCH /api/v1/alerts/{alert_id}/acknowledge` marks an alert as acknowledged
- Alerts are generated in near-real-time when telemetry breaches a threshold
- An alert includes: device info, the breached metric, threshold value, actual value, severity, and timestamp
- Default threshold rules are seeded on startup for common drilling parameters

### Feature 4: IoT Device Simulator

Realistic sensor data generation for demonstration and testing.

**Acceptance Criteria:**
- Simulator registers N configurable devices on startup (default: 3 rigs)
- Generates readings for 5 drilling parameters: RPM, WOB (klbs), torque (kNm), mud flow rate (L/min), vibration (g)
- Normal readings follow realistic distributions with minor noise
- Anomaly mode: periodically injects spikes (e.g., vibration surge) to trigger alerts
- Configurable via environment variables: `SIM_DEVICE_COUNT`, `SIM_INTERVAL_SECONDS`, `SIM_ANOMALY_PROBABILITY`
- Logs each POST with device ID and response status

### Feature 5: Monitoring Dashboard

Web-based equipment monitoring interface.

**Acceptance Criteria:**
- Dashboard shows an overview page with all devices and their current status (color-coded: green/yellow/red)
- Clicking a device shows real-time telemetry charts (line charts for each parameter over the last 10 minutes)
- An alerts panel shows active alerts sorted by severity, with acknowledge button
- Auto-refreshes every 5 seconds
- Accessible at `http://localhost:8501` after `docker compose up`

### Feature 6: Health & Integration Endpoints

Operational endpoints for monitoring the platform itself.

**Acceptance Criteria:**
- `GET /api/v1/health` returns service health including DB connectivity status
- `GET /api/v1/stats` returns platform statistics: total devices, total readings ingested, active alerts count
- API serves OpenAPI/Swagger docs at `/docs`
- All API responses include consistent envelope: `{"data": ..., "meta": {"timestamp": "..."}}`

---

## 5. Data Models

### Entity Relationship

```
Device  1──────N  TelemetryReading
Device  1──────N  Alert
AlertRule  1───N  Alert
```

### Database Schema

#### `devices`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK, default gen_random_uuid() |
| `name` | VARCHAR(255) | NOT NULL, UNIQUE |
| `device_type` | VARCHAR(100) | NOT NULL (e.g., "drilling_rig", "mud_pump") |
| `location` | VARCHAR(255) | NOT NULL |
| `metadata` | JSONB | Optional extra fields |
| `created_at` | TIMESTAMPTZ | NOT NULL, default now() |
| `last_seen_at` | TIMESTAMPTZ | Nullable, updated on each telemetry POST |

#### `telemetry_readings`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | BIGSERIAL | PK |
| `device_id` | UUID | FK → devices.id, NOT NULL |
| `timestamp` | TIMESTAMPTZ | NOT NULL |
| `rpm` | FLOAT | Rotary speed (0-300) |
| `wob` | FLOAT | Weight on bit, klbs (0-100) |
| `torque` | FLOAT | kNm (0-100) |
| `mud_flow_rate` | FLOAT | L/min (0-5000) |
| `vibration` | FLOAT | g-force (0-20) |

**Index:** `(device_id, timestamp DESC)` — optimizes time-range queries per device.

#### `alert_rules`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `name` | VARCHAR(255) | NOT NULL |
| `metric` | VARCHAR(50) | NOT NULL (rpm, wob, torque, mud_flow_rate, vibration) |
| `operator` | VARCHAR(10) | NOT NULL (gt, lt, gte, lte) |
| `threshold_value` | FLOAT | NOT NULL |
| `severity` | VARCHAR(20) | NOT NULL (low, medium, high, critical) |
| `device_type` | VARCHAR(100) | Nullable — if set, rule applies only to this device type |
| `is_active` | BOOLEAN | Default true |
| `created_at` | TIMESTAMPTZ | NOT NULL |

#### `alerts`
| Column | Type | Constraints |
|--------|------|-------------|
| `id` | UUID | PK |
| `device_id` | UUID | FK → devices.id, NOT NULL |
| `rule_id` | UUID | FK → alert_rules.id, NOT NULL |
| `metric` | VARCHAR(50) | NOT NULL |
| `threshold_value` | FLOAT | NOT NULL |
| `actual_value` | FLOAT | NOT NULL |
| `severity` | VARCHAR(20) | NOT NULL |
| `message` | TEXT | Human-readable alert description |
| `acknowledged` | BOOLEAN | Default false |
| `acknowledged_at` | TIMESTAMPTZ | Nullable |
| `created_at` | TIMESTAMPTZ | NOT NULL |

---

## 6. API Design

### Base URL
`http://localhost:8000/api/v1`

### Response Envelope
All responses follow a consistent format:
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-04-03T12:00:00Z",
    "count": 10
  }
}
```

### Endpoints

#### Devices

**POST /devices** — Register a new device
```json
// Request
{
  "name": "Rig Alpha-1",
  "device_type": "drilling_rig",
  "location": "North Sea Platform A",
  "metadata": {"model": "HMH-500", "firmware": "3.2.1"}
}
// Response 201
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Rig Alpha-1",
    "device_type": "drilling_rig",
    "location": "North Sea Platform A",
    "status": "offline",
    "created_at": "2026-04-03T12:00:00Z"
  }
}
```

**GET /devices** — List all devices
```
Query params: ?status=online|offline|alert
```

**GET /devices/{device_id}** — Get device details with current status

#### Telemetry

**POST /telemetry** — Ingest sensor readings
```json
// Request
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "readings": [
    {
      "timestamp": "2026-04-03T12:00:00.123Z",
      "rpm": 120.5,
      "wob": 35.2,
      "torque": 22.1,
      "mud_flow_rate": 2800.0,
      "vibration": 3.4
    }
  ]
}
// Response 201
{
  "data": {"ingested": 1},
  "meta": {"timestamp": "2026-04-03T12:00:00Z"}
}
```

**GET /telemetry/{device_id}** — Query historical readings
```
Query params: ?start=ISO8601&end=ISO8601&limit=100&offset=0
```

**GET /telemetry/{device_id}/latest** — Most recent reading

#### Alerts

**GET /alerts** — List alerts
```
Query params: ?device_id=UUID&severity=high&acknowledged=false&limit=50
```

**POST /alerts/rules** — Create a threshold rule
```json
// Request
{
  "name": "High Vibration Warning",
  "metric": "vibration",
  "operator": "gt",
  "threshold_value": 8.0,
  "severity": "high",
  "device_type": "drilling_rig"
}
```

**GET /alerts/rules** — List all alert rules

**PATCH /alerts/{alert_id}/acknowledge** — Acknowledge an alert
```json
// Response 200
{
  "data": {
    "id": "...",
    "acknowledged": true,
    "acknowledged_at": "2026-04-03T12:05:00Z"
  }
}
```

#### Operational

**GET /health** — Service health
```json
{
  "data": {
    "status": "healthy",
    "database": "connected",
    "uptime_seconds": 3600
  }
}
```

**GET /stats** — Platform statistics
```json
{
  "data": {
    "total_devices": 3,
    "online_devices": 2,
    "total_readings": 15420,
    "active_alerts": 1
  }
}
```

---

## 7. Testing Strategy

### Unit Tests
- **Scope:** Business logic in isolation — alert threshold evaluation, telemetry validation, device status calculation
- **Approach:** pytest with fixtures. Mock database calls using dependency injection (FastAPI's `Depends` override)
- **Key areas:**
  - Telemetry validation: boundary values, missing fields, invalid ranges
  - Alert rule matching: each operator type, edge cases at threshold boundaries
  - Device status logic: online/offline/alert state transitions based on timing

### Integration Tests
- **Scope:** Full API request/response cycles against a real PostgreSQL instance
- **Approach:** pytest with `httpx.AsyncClient` and a test database (separate Docker container or test schema)
- **Key areas:**
  - Device CRUD lifecycle
  - Telemetry ingestion → alert generation flow (post telemetry that breaches a threshold, verify alert created)
  - Pagination and filtering on telemetry and alert queries
  - Error responses: 404, 409, 422 with correct bodies

### CI Pipeline (GitHub Actions)
```yaml
on: [push, pull_request]
jobs:
  lint:    ruff check + ruff format --check
  test:    pytest with PostgreSQL service container, coverage report
  build:   docker compose build (verify all images build successfully)
```

### What NOT to Test
- Streamlit UI (visual; manual verification is sufficient)
- Simulator internals beyond basic config parsing (it's a demo tool, not production code)

---

## 8. Infrastructure & Deployment

### Docker Compose Services

| Service | Image | Ports | Purpose |
|---------|-------|-------|---------|
| `api` | Custom (Dockerfile) | 8000:8000 | FastAPI backend |
| `db` | postgres:16-alpine | 5432:5432 | PostgreSQL database |
| `simulator` | Custom (Dockerfile) | — | IoT device simulator (no exposed port) |
| `dashboard` | Custom (Dockerfile) | 8501:8501 | Streamlit web UI |

### Startup Order
1. `db` starts first (healthcheck: `pg_isready`)
2. `api` waits for `db` healthy, runs Alembic migrations on startup, then serves
3. `simulator` waits for `api` healthy, registers devices, begins sending telemetry
4. `dashboard` waits for `api` healthy, then serves UI

### Environment Variables
All configuration via environment variables with sensible defaults in `docker-compose.yml`:

```
DATABASE_URL=postgresql+asyncpg://drillsense:drillsense@db:5432/drillsense
API_HOST=0.0.0.0
API_PORT=8000
SIM_DEVICE_COUNT=3
SIM_INTERVAL_SECONDS=2
SIM_ANOMALY_PROBABILITY=0.05
```

### Running Locally
```bash
docker compose up --build
# API:       http://localhost:8000/docs
# Dashboard: http://localhost:8501
```

No cloud accounts, API keys, or external services required.

---

## 9. Project Structure

```
drillsense/
├── docker-compose.yml
├── docs/
│   └── PRD.md
├── .github/
│   └── workflows/
│       └── ci.yml                  # Lint, test, build pipeline
├── api/
│   ├── Dockerfile
│   ├── pyproject.toml              # Dependencies: fastapi, sqlalchemy, asyncpg, alembic, uvicorn
│   ├── alembic/
│   │   ├── alembic.ini
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial.py      # Initial schema migration
│   ├── src/
│   │   └── drillsense/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI app, lifespan, middleware
│   │       ├── config.py           # Settings from environment
│   │       ├── database.py         # Async SQLAlchemy engine and session
│   │       ├── models.py           # SQLAlchemy ORM models
│   │       ├── schemas.py          # Pydantic request/response schemas
│   │       ├── routers/
│   │       │   ├── __init__.py
│   │       │   ├── devices.py      # Device CRUD endpoints
│   │       │   ├── telemetry.py    # Telemetry ingestion and query endpoints
│   │       │   ├── alerts.py       # Alert and rule endpoints
│   │       │   └── health.py       # Health and stats endpoints
│   │       └── services/
│   │           ├── __init__.py
│   │           ├── device_service.py
│   │           ├── telemetry_service.py
│   │           └── alert_service.py  # Threshold evaluation logic
│   └── tests/
│       ├── conftest.py             # Fixtures: test DB, async client, sample data
│       ├── test_devices.py
│       ├── test_telemetry.py
│       └── test_alerts.py
├── simulator/
│   ├── Dockerfile
│   ├── pyproject.toml              # Dependencies: httpx
│   └── src/
│       └── simulator/
│           ├── __init__.py
│           ├── main.py             # Entry point: register devices, run loop
│           ├── generators.py       # Sensor data generators with noise + anomalies
│           └── config.py           # Simulator settings from environment
└── dashboard/
    ├── Dockerfile
    ├── pyproject.toml              # Dependencies: streamlit, httpx, plotly
    └── src/
        └── dashboard/
            ├── app.py              # Streamlit app entry point
            ├── pages/
            │   ├── overview.py     # Device status grid
            │   └── device.py       # Per-device telemetry charts + alerts
            └── api_client.py       # Typed wrapper around the REST API
```

---

## Summary

DrillSense is a focused, backend-heavy industrial IoT platform that maps directly to HMH's domain. It demonstrates:

- **Backend Services & APIs** — FastAPI with structured routers, services, and Pydantic validation
- **IoT Integration** — Device simulator posting telemetry over HTTP, mimicking real field equipment
- **REST API Design** — Versioned, documented, consistent envelope, proper HTTP semantics
- **CI/CD** — GitHub Actions pipeline with lint, test, and build stages
- **DevOps & Containers** — Full Docker Compose setup, health checks, migration-on-startup
- **Automated Testing** — Unit and integration tests with pytest against real PostgreSQL
- **Secure Data Platform Thinking** — Input validation, structured data models, operational health endpoints
- **Integration** — Multiple services communicating through well-defined APIs

Total scope: ~1,500-2,000 lines of application code. Achievable as a single-developer project in a focused implementation sprint.
