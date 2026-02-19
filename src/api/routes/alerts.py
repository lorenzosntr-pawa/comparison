"""Risk alert API endpoints.

This module provides endpoints for managing risk alerts:
- GET /alerts: List alerts with filters
- GET /alerts/stats: Summary statistics
- GET /alerts/{alert_id}: Get single alert
- PATCH /alerts/{alert_id}: Acknowledge/unacknowledge alert
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.alerts import (
    AcknowledgeAlertRequest,
    RiskAlertResponse,
    RiskAlertsResponse,
    RiskAlertStatsResponse,
)
from src.db.engine import get_db

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=RiskAlertsResponse)
async def list_alerts(
    status: str | None = Query(None, description="Filter by status (new, acknowledged, past)"),
    severity: str | None = Query(None, description="Filter by severity (warning, elevated, critical)"),
    alert_type: str | None = Query(None, description="Filter by alert type (price_change, direction_disagreement, availability)"),
    event_id: int | None = Query(None, description="Filter by event ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    db: AsyncSession = Depends(get_db),
) -> RiskAlertsResponse:
    """List risk alerts with optional filters.

    Returns paginated alerts with counts by status for status bar.

    Args:
        status: Filter by workflow status (new, acknowledged, past).
        severity: Filter by severity level (warning, elevated, critical).
        alert_type: Filter by alert type (price_change, direction_disagreement, availability).
        event_id: Filter by specific event ID.
        limit: Maximum number of alerts to return (1-200, default 50).
        offset: Number of alerts to skip for pagination.
        db: Async database session (injected).

    Returns:
        RiskAlertsResponse with filtered alerts and status counts.
    """
    # Deferred import to avoid circular dependency
    from src.db.models.event import Event
    from src.db.models.risk_alert import RiskAlert

    # Build base query with filters
    query = select(RiskAlert)
    if status:
        query = query.where(RiskAlert.status == status)
    if severity:
        query = query.where(RiskAlert.severity == severity)
    if alert_type:
        query = query.where(RiskAlert.alert_type == alert_type)
    if event_id:
        query = query.where(RiskAlert.event_id == event_id)

    # Order by most recent first
    query = query.order_by(desc(RiskAlert.detected_at))

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()

    # Fetch event details for all alerts
    event_ids = list({a.event_id for a in alerts})
    events_by_id: dict[int, Event] = {}
    if event_ids:
        events_result = await db.execute(
            select(Event).where(Event.id.in_(event_ids))
        )
        events_by_id = {e.id: e for e in events_result.scalars().all()}

    # Build response with event details
    alert_responses = []
    for alert in alerts:
        event = events_by_id.get(alert.event_id)
        response = RiskAlertResponse.model_validate(alert)
        if event:
            response.event_name = event.name
            response.home_team = event.home_team
            response.away_team = event.away_team
        alert_responses.append(response)

    # Get status counts for all alerts (not just filtered)
    status_counts_query = (
        select(RiskAlert.status, func.count(RiskAlert.id))
        .group_by(RiskAlert.status)
    )
    status_result = await db.execute(status_counts_query)
    status_counts = dict(status_result.fetchall())

    return RiskAlertsResponse(
        alerts=alert_responses,
        total=total,
        new_count=status_counts.get("new", 0),
        acknowledged_count=status_counts.get("acknowledged", 0),
        past_count=status_counts.get("past", 0),
    )


@router.get("/stats", response_model=RiskAlertStatsResponse)
async def get_alert_stats(
    db: AsyncSession = Depends(get_db),
) -> RiskAlertStatsResponse:
    """Get summary statistics for risk alerts.

    Returns counts grouped by status, severity, and alert type.

    Args:
        db: Async database session (injected).

    Returns:
        RiskAlertStatsResponse with grouped counts.
    """
    from src.db.models.risk_alert import RiskAlert

    # Get total count
    total_result = await db.execute(select(func.count(RiskAlert.id)))
    total = total_result.scalar_one()

    # Group by status
    status_query = (
        select(RiskAlert.status, func.count(RiskAlert.id))
        .group_by(RiskAlert.status)
    )
    status_result = await db.execute(status_query)
    by_status = dict(status_result.fetchall())

    # Group by severity
    severity_query = (
        select(RiskAlert.severity, func.count(RiskAlert.id))
        .group_by(RiskAlert.severity)
    )
    severity_result = await db.execute(severity_query)
    by_severity = dict(severity_result.fetchall())

    # Group by alert type
    type_query = (
        select(RiskAlert.alert_type, func.count(RiskAlert.id))
        .group_by(RiskAlert.alert_type)
    )
    type_result = await db.execute(type_query)
    by_type = dict(type_result.fetchall())

    return RiskAlertStatsResponse(
        total=total,
        by_status=by_status,
        by_severity=by_severity,
        by_type=by_type,
    )


@router.get("/{alert_id}", response_model=RiskAlertResponse)
async def get_alert(
    alert_id: int = Path(..., description="Alert ID to retrieve"),
    db: AsyncSession = Depends(get_db),
) -> RiskAlertResponse:
    """Get a single risk alert by ID.

    Args:
        alert_id: ID of the alert to retrieve.
        db: Async database session (injected).

    Returns:
        RiskAlertResponse with alert details.

    Raises:
        HTTPException: 404 if alert not found.
    """
    from src.db.models.risk_alert import RiskAlert

    result = await db.execute(
        select(RiskAlert).where(RiskAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return RiskAlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=RiskAlertResponse)
async def acknowledge_alert(
    request: AcknowledgeAlertRequest,
    alert_id: int = Path(..., description="Alert ID to acknowledge"),
    db: AsyncSession = Depends(get_db),
) -> RiskAlertResponse:
    """Acknowledge or unacknowledge a risk alert.

    Sets status to 'acknowledged' with timestamp when acknowledged=True,
    or reverts to 'new' with null timestamp when acknowledged=False.

    Cannot acknowledge alerts that have already transitioned to PAST status.

    Args:
        request: AcknowledgeAlertRequest with acknowledged boolean.
        alert_id: ID of the alert to update.
        db: Async database session (injected).

    Returns:
        Updated RiskAlertResponse.

    Raises:
        HTTPException: 404 if alert not found, 400 if alert is PAST.
    """
    from src.db.models.risk_alert import RiskAlert

    result = await db.execute(
        select(RiskAlert).where(RiskAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status == "past":
        raise HTTPException(
            status_code=400,
            detail="Cannot modify PAST alerts (event has started)"
        )

    if request.acknowledged:
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        alert.status = "new"
        alert.acknowledged_at = None

    await db.commit()
    await db.refresh(alert)

    return RiskAlertResponse.model_validate(alert)
