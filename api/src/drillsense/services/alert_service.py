import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from drillsense.models import Alert, AlertRule, Device, TelemetryReading

OPERATOR_MAP = {
    "gt": lambda actual, threshold: actual > threshold,
    "lt": lambda actual, threshold: actual < threshold,
    "gte": lambda actual, threshold: actual >= threshold,
    "lte": lambda actual, threshold: actual <= threshold,
}


async def create_rule(session: AsyncSession, **kwargs) -> AlertRule:
    rule = AlertRule(**kwargs)
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def list_rules(session: AsyncSession) -> list[AlertRule]:
    result = await session.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
    return list(result.scalars().all())


async def evaluate_telemetry(
    session: AsyncSession,
    device: Device,
    reading: TelemetryReading,
) -> list[Alert]:
    """Evaluate a telemetry reading against all active alert rules."""
    result = await session.execute(select(AlertRule).where(AlertRule.is_active == True))  # noqa: E712
    rules = list(result.scalars().all())

    new_alerts: list[Alert] = []
    for rule in rules:
        if rule.device_type and rule.device_type != device.device_type:
            continue

        actual_value = getattr(reading, rule.metric, None)
        if actual_value is None:
            continue

        check = OPERATOR_MAP.get(rule.operator)
        if check and check(actual_value, rule.threshold_value):
            op_display = {"gt": ">", "lt": "<", "gte": ">=", "lte": "<="}.get(
                rule.operator, rule.operator
            )
            alert = Alert(
                device_id=device.id,
                rule_id=rule.id,
                metric=rule.metric,
                threshold_value=rule.threshold_value,
                actual_value=actual_value,
                severity=rule.severity,
                message=(
                    f"{rule.name}: {rule.metric} = {actual_value:.2f} "
                    f"(threshold {op_display} {rule.threshold_value})"
                ),
            )
            session.add(alert)
            new_alerts.append(alert)

    if new_alerts:
        await session.commit()
    return new_alerts


async def list_alerts(
    session: AsyncSession,
    device_id: uuid.UUID | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    limit: int = 50,
) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if device_id:
        stmt = stmt.where(Alert.device_id == device_id)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if acknowledged is not None:
        stmt = stmt.where(Alert.acknowledged == acknowledged)
    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def acknowledge_alert(session: AsyncSession, alert_id: uuid.UUID) -> Alert | None:
    alert = await session.get(Alert, alert_id)
    if alert is None:
        return None
    alert.acknowledged = True
    alert.acknowledged_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(alert)
    return alert


async def count_active_alerts(session: AsyncSession) -> int:
    result = await session.execute(
        select(Alert.id).where(Alert.acknowledged == False)  # noqa: E712
    )
    return len(result.all())


async def seed_default_rules(session: AsyncSession) -> None:
    """Seed default alert rules if none exist."""
    result = await session.execute(select(AlertRule).limit(1))
    if result.scalar_one_or_none() is not None:
        return

    defaults = [
        AlertRule(
            name="High Vibration Warning",
            metric="vibration",
            operator="gt",
            threshold_value=8.0,
            severity="high",
            device_type="drilling_rig",
        ),
        AlertRule(
            name="Critical Vibration",
            metric="vibration",
            operator="gt",
            threshold_value=12.0,
            severity="critical",
            device_type="drilling_rig",
        ),
        AlertRule(
            name="Excessive RPM",
            metric="rpm",
            operator="gt",
            threshold_value=250.0,
            severity="high",
        ),
        AlertRule(
            name="High Torque Warning",
            metric="torque",
            operator="gt",
            threshold_value=80.0,
            severity="medium",
        ),
        AlertRule(
            name="Low Mud Flow",
            metric="mud_flow_rate",
            operator="lt",
            threshold_value=500.0,
            severity="high",
        ),
    ]
    session.add_all(defaults)
    await session.commit()
