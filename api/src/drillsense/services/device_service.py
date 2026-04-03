import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.config import settings
from drillsense.models import Alert, Device


def compute_device_status(device: Device) -> str:
    """Determine device status based on last_seen_at and active alerts."""
    if device.last_seen_at is None:
        return "offline"
    threshold = datetime.now(UTC) - timedelta(seconds=settings.device_offline_threshold_seconds)
    if device.last_seen_at.replace(tzinfo=UTC) < threshold:
        return "offline"
    return "online"


async def create_device(
    session: AsyncSession,
    name: str,
    device_type: str,
    location: str,
    metadata: dict | None = None,
) -> Device:
    device = Device(name=name, device_type=device_type, location=location, metadata_=metadata)
    session.add(device)
    try:
        await session.commit()
        await session.refresh(device)
    except IntegrityError:
        await session.rollback()
        raise
    return device


async def get_device(session: AsyncSession, device_id: uuid.UUID) -> Device | None:
    return await session.get(Device, device_id)


async def list_devices(session: AsyncSession, status_filter: str | None = None) -> list[Device]:
    result = await session.execute(select(Device).order_by(Device.created_at.desc()))
    devices = list(result.scalars().all())
    if status_filter:
        devices = [d for d in devices if compute_device_status(d) == status_filter]
    return devices


async def has_active_alerts(session: AsyncSession, device_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Alert.id)
        .where(Alert.device_id == device_id, Alert.acknowledged == False)  # noqa: E712
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def get_device_status(session: AsyncSession, device: Device) -> str:
    base_status = compute_device_status(device)
    if base_status == "online" and await has_active_alerts(session, device.id):
        return "alert"
    return base_status
