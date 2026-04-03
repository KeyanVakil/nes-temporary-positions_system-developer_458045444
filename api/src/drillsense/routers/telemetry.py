import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.database import get_session
from drillsense.models import TelemetryReading
from drillsense.schemas import Envelope, Meta, TelemetryIngest, TelemetryResponse
from drillsense.services import alert_service, device_service, telemetry_service

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", status_code=201, response_model=Envelope)
async def ingest_telemetry(
    body: TelemetryIngest,
    session: AsyncSession = Depends(get_session),
):
    device = await device_service.get_device(session, body.device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    readings_dicts = [r.model_dump() for r in body.readings]
    count = await telemetry_service.ingest_readings(session, body.device_id, readings_dicts)

    # Evaluate alert rules against each new reading
    await session.refresh(device)
    for r in body.readings:
        reading = TelemetryReading(device_id=body.device_id, **r.model_dump())
        await alert_service.evaluate_telemetry(session, device, reading)

    return Envelope(data={"ingested": count})


@router.get("/{device_id}", response_model=Envelope)
async def get_telemetry(
    device_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
):
    device = await device_service.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    readings = await telemetry_service.get_readings(session, device_id, start, end, limit, offset)
    data = [TelemetryResponse.model_validate(r) for r in readings]
    return Envelope(data=data, meta=Meta(count=len(data)))


@router.get("/{device_id}/latest", response_model=Envelope)
async def get_latest_telemetry(
    device_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    device = await device_service.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    reading = await telemetry_service.get_latest_reading(session, device_id)
    if reading is None:
        return Envelope(data=None)
    return Envelope(data=TelemetryResponse.model_validate(reading))
