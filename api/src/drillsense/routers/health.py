import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.database import get_session
from drillsense.schemas import Envelope, HealthResponse, StatsResponse
from drillsense.services import alert_service, device_service, telemetry_service

router = APIRouter(tags=["health"])

_start_time = time.monotonic()


@router.get("/health", response_model=Envelope)
async def health_check(session: AsyncSession = Depends(get_session)):
    db_status = "connected"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    data = HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        uptime_seconds=round(time.monotonic() - _start_time, 1),
    )
    return Envelope(data=data)


@router.get("/stats", response_model=Envelope)
async def stats(session: AsyncSession = Depends(get_session)):
    devices = await device_service.list_devices(session)
    online = sum(1 for d in devices if device_service.compute_device_status(d) == "online")
    total_readings = await telemetry_service.count_readings(session)
    active_alerts = await alert_service.count_active_alerts(session)

    data = StatsResponse(
        total_devices=len(devices),
        online_devices=online,
        total_readings=total_readings,
        active_alerts=active_alerts,
    )
    return Envelope(data=data)
