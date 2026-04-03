# DrillSense — Industrial Equipment Telemetry Platform

A backend-focused industrial IoT platform that ingests, processes, stores, and visualizes telemetry data from drilling equipment sensors. Built as a demonstration project for the System Developer position at NES Fircroft / HMH.

**Job listing:** https://www.finn.no/job/ad/458045444

## Skills Demonstrated

| Job Requirement | Where It's Demonstrated |
|----------------|------------------------|
| Backend services & APIs | FastAPI REST API with versioned endpoints, Pydantic validation, service layer |
| IoT / integration | Device simulator posting telemetry over HTTP, mimicking real field equipment |
| REST API design | Consistent response envelope, proper HTTP semantics, OpenAPI docs |
| CI/CD pipelines | GitHub Actions with lint, test, and Docker build stages |
| DevOps & containers | Full Docker Compose setup, health checks, migration-on-startup |
| Automated testing | Unit and integration tests with pytest against real database |
| Database design | PostgreSQL with time-series indexing, Alembic migrations |
| Secure data platform | Input validation, typed schemas, operational health endpoints |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                      │
│                                                               │
│  ┌──────────────┐     ┌──────────────────┐                   │
│  │  IoT Device   │────▶│   Ingestion API   │                  │
│  │  Simulator    │ HTTP│   (FastAPI)        │                  │
│  │  (Python)     │     │                    │                  │
│  └──────────────┘     └────────┬───────────┘                 │
│                                 │                              │
│                        ┌────────▼───────────┐                 │
│                        │   PostgreSQL 16     │                 │
│                        │   (Time-series +    │                 │
│                        │    device registry) │                 │
│                        └────────┬───────────┘                 │
│                                 │                              │
│                        ┌────────▼───────────┐                 │
│                        │   Alert Engine      │                 │
│                        │   (Threshold checks)│                 │
│                        └────────┬───────────┘                 │
│                                 │                              │
│                        ┌────────▼───────────┐                 │
│                        │   Web Dashboard     │                 │
│                        │   (Streamlit)       │                 │
│                        └────────────────────┘                 │
└──────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
docker compose up --build
```

Then open:
- **Dashboard:** http://localhost:8501
- **API docs (Swagger):** http://localhost:8000/docs
- **API health:** http://localhost:8000/api/v1/health

The simulator automatically registers 3 drilling rigs and begins sending telemetry every 2 seconds. Anomalies are injected with 5% probability to trigger alerts.

## Running Tests

```bash
cd api
pip install -e ".[dev]"
PYTHONPATH=src pytest tests/ -v
```

Tests use SQLite for fast execution without requiring PostgreSQL.

## Tech Stack

| Technology | Role | Rationale |
|-----------|------|-----------|
| Python 3.12 | Primary language | Industry-standard for backend services and IoT |
| FastAPI | REST API | Async-capable, auto OpenAPI docs, Pydantic validation |
| PostgreSQL 16 | Database | Robust relational DB with time-series query support |
| SQLAlchemy 2.x | ORM | Type-safe async database access |
| Alembic | Migrations | Versioned schema changes — standard DevOps practice |
| Streamlit | Dashboard | Rapid data-app development for monitoring UIs |
| Docker Compose | Infrastructure | Single command to run all 4 services |
| pytest | Testing | Unit + integration tests with async support |
| Ruff | Linting | Fast Python linter and formatter |
| GitHub Actions | CI/CD | Lint, test, and build on every push |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/devices` | Register a new device |
| GET | `/api/v1/devices` | List all devices |
| GET | `/api/v1/devices/{id}` | Get device details |
| POST | `/api/v1/telemetry` | Ingest sensor readings |
| GET | `/api/v1/telemetry/{device_id}` | Query historical readings |
| GET | `/api/v1/telemetry/{device_id}/latest` | Latest reading |
| GET | `/api/v1/alerts` | List alerts |
| PATCH | `/api/v1/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/api/v1/alerts/rules` | Create threshold rule |
| GET | `/api/v1/alerts/rules` | List alert rules |
| GET | `/api/v1/health` | Service health check |
| GET | `/api/v1/stats` | Platform statistics |

## Project Structure

```
├── docker-compose.yml
├── api/
│   ├── Dockerfile
│   ├── alembic/              # Database migrations
│   ├── src/drillsense/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── schemas.py        # Pydantic request/response schemas
│   │   ├── routers/          # API endpoint handlers
│   │   └── services/         # Business logic layer
│   └── tests/                # Unit + integration tests
├── simulator/
│   └── src/simulator/        # IoT device simulator
├── dashboard/
│   └── src/dashboard/        # Streamlit monitoring UI
└── .github/workflows/ci.yml  # CI pipeline
```
