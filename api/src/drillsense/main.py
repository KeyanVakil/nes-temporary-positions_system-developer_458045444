from contextlib import asynccontextmanager

from fastapi import FastAPI

from drillsense.database import async_session
from drillsense.routers import alerts, devices, health, telemetry
from drillsense.services.alert_service import seed_default_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session() as session:
        await seed_default_rules(session)
    yield


app = FastAPI(
    title="DrillSense API",
    description="Industrial Equipment Telemetry Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(devices.router, prefix="/api/v1")
app.include_router(telemetry.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
