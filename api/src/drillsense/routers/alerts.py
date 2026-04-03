import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.database import get_session
from drillsense.schemas import (
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    Envelope,
    Meta,
)
from drillsense.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=Envelope)
async def list_alerts(
    device_id: uuid.UUID | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    alerts = await alert_service.list_alerts(session, device_id, severity, acknowledged, limit)
    data = [AlertResponse.model_validate(a) for a in alerts]
    return Envelope(data=data, meta=Meta(count=len(data)))


@router.patch("/{alert_id}/acknowledge", response_model=Envelope)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    alert = await alert_service.acknowledge_alert(session, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return Envelope(data=AlertResponse.model_validate(alert))


@router.post("/rules", status_code=201, response_model=Envelope)
async def create_rule(
    body: AlertRuleCreate,
    session: AsyncSession = Depends(get_session),
):
    rule = await alert_service.create_rule(
        session,
        name=body.name,
        metric=body.metric,
        operator=body.operator,
        threshold_value=body.threshold_value,
        severity=body.severity,
        device_type=body.device_type,
    )
    return Envelope(data=AlertRuleResponse.model_validate(rule))


@router.get("/rules", response_model=Envelope)
async def list_rules(
    session: AsyncSession = Depends(get_session),
):
    rules = await alert_service.list_rules(session)
    data = [AlertRuleResponse.model_validate(r) for r in rules]
    return Envelope(data=data, meta=Meta(count=len(data)))
