import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.database import get_session
from drillsense.schemas import DeviceCreate, DeviceResponse, Envelope, Meta
from drillsense.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", status_code=201, response_model=Envelope)
async def create_device(
    body: DeviceCreate,
    session: AsyncSession = Depends(get_session),
):
    try:
        device = await device_service.create_device(
            session, body.name, body.device_type, body.location, body.metadata
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Device with name '{body.name}' already exists",
        ) from exc

    status = await device_service.get_device_status(session, device)
    resp = DeviceResponse(
        id=device.id,
        name=device.name,
        device_type=device.device_type,
        location=device.location,
        metadata=device.metadata_,
        status=status,
        created_at=device.created_at,
        last_seen_at=device.last_seen_at,
    )
    return Envelope(data=resp)


@router.get("", response_model=Envelope)
async def list_devices(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    devices = await device_service.list_devices(session, status_filter=status)
    result = []
    for d in devices:
        s = await device_service.get_device_status(session, d)
        result.append(
            DeviceResponse(
                id=d.id,
                name=d.name,
                device_type=d.device_type,
                location=d.location,
                metadata=d.metadata_,
                status=s,
                created_at=d.created_at,
                last_seen_at=d.last_seen_at,
            )
        )
    return Envelope(data=result, meta=Meta(count=len(result)))


@router.get("/{device_id}", response_model=Envelope)
async def get_device(
    device_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    device = await device_service.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    status = await device_service.get_device_status(session, device)
    resp = DeviceResponse(
        id=device.id,
        name=device.name,
        device_type=device.device_type,
        location=device.location,
        metadata=device.metadata_,
        status=status,
        created_at=device.created_at,
        last_seen_at=device.last_seen_at,
    )
    return Envelope(data=resp)
