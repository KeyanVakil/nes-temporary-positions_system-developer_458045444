import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.models import Device, TelemetryReading


async def ingest_readings(
    session: AsyncSession,
    device_id: uuid.UUID,
    readings: list[dict],
) -> int:
    device = await session.get(Device, device_id)
    if device is None:
        raise ValueError(f"Device {device_id} not found")

    db_readings = []
    latest_ts = device.last_seen_at
    for r in readings:
        reading = TelemetryReading(device_id=device_id, **r)
        db_readings.append(reading)
        ts = r["timestamp"]
        # Normalize both to naive UTC for comparison
        ts_cmp = ts.replace(tzinfo=None) if hasattr(ts, "replace") else ts
        latest_cmp = (
            latest_ts.replace(tzinfo=None)
            if latest_ts and hasattr(latest_ts, "replace")
            else latest_ts
        )
        if latest_cmp is None or ts_cmp > latest_cmp:
            latest_ts = ts

    session.add_all(db_readings)
    device.last_seen_at = latest_ts
    await session.commit()
    return len(db_readings)


async def get_readings(
    session: AsyncSession,
    device_id: uuid.UUID,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[TelemetryReading]:
    stmt = (
        select(TelemetryReading)
        .where(TelemetryReading.device_id == device_id)
        .order_by(TelemetryReading.timestamp.desc())
    )
    if start:
        stmt = stmt.where(TelemetryReading.timestamp >= start)
    if end:
        stmt = stmt.where(TelemetryReading.timestamp <= end)
    stmt = stmt.offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_latest_reading(
    session: AsyncSession, device_id: uuid.UUID
) -> TelemetryReading | None:
    stmt = (
        select(TelemetryReading)
        .where(TelemetryReading.device_id == device_id)
        .order_by(TelemetryReading.timestamp.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def count_readings(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(TelemetryReading.id)))
    return result.scalar_one()
