"""Pydantic schemas for risk alert API endpoints.

This module defines request and response schemas for risk alert management:
- RiskAlertResponse: Individual alert details
- RiskAlertsResponse: Paginated list with status counts
- RiskAlertStatsResponse: Summary statistics by status/severity/type
- AcknowledgeAlertRequest: Request body for acknowledge/unacknowledge

Uses camelCase aliases for frontend compatibility.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class RiskAlertResponse(BaseModel):
    """Response model for a single risk alert.

    Attributes:
        id: Unique database ID.
        event_id: FK to events table.
        bookmaker_slug: Which bookmaker triggered the alert.
        market_id: Betpawa market ID affected.
        market_name: Human-readable market name.
        line: Line value for total/handicap markets (nullable).
        outcome_name: Specific outcome if applicable (nullable).
        alert_type: Type of alert (price_change, direction_disagreement, availability).
        severity: Severity level (warning, elevated, critical).
        change_percent: Absolute percentage change.
        old_value: Previous odds value (nullable).
        new_value: Current odds value (nullable).
        competitor_direction: For disagreement alerts (nullable).
        detected_at: When the alert was detected.
        acknowledged_at: When user acknowledged (nullable).
        status: Current workflow status (new, acknowledged, past).
        event_kickoff: Kickoff time for the event.
    """

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int = Field(description="Unique database ID")
    event_id: int = Field(description="FK to events table")
    event_name: str | None = Field(None, description="Event display name (home vs away)")
    home_team: str | None = Field(None, description="Home team name")
    away_team: str | None = Field(None, description="Away team name")
    bookmaker_slug: str = Field(description="Bookmaker that triggered alert")
    market_id: str = Field(description="Betpawa market ID")
    market_name: str = Field(description="Human-readable market name")
    line: float | None = Field(description="Line value for totals/handicaps")
    outcome_name: str | None = Field(description="Specific outcome affected")
    alert_type: str = Field(description="Alert type (price_change, direction_disagreement, availability)")
    severity: str = Field(description="Severity level (warning, elevated, critical)")
    change_percent: float = Field(description="Absolute percentage change")
    old_value: float | None = Field(description="Previous odds value")
    new_value: float | None = Field(description="Current odds value")
    competitor_direction: str | None = Field(description="Direction disagreement info")
    detected_at: datetime = Field(description="When alert was detected")
    acknowledged_at: datetime | None = Field(description="When user acknowledged")
    status: str = Field(description="Workflow status (new, acknowledged, past)")
    event_kickoff: datetime = Field(description="Event kickoff time")


class RiskAlertsResponse(BaseModel):
    """Response model for paginated risk alerts list.

    Attributes:
        alerts: List of risk alert records.
        total: Total number of alerts matching filters.
        new_count: Count of alerts with status 'new'.
        acknowledged_count: Count of alerts with status 'acknowledged'.
        past_count: Count of alerts with status 'past'.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    alerts: list[RiskAlertResponse] = Field(description="Risk alert records")
    total: int = Field(description="Total matching alerts")
    new_count: int = Field(description="Count of NEW alerts")
    acknowledged_count: int = Field(description="Count of ACKNOWLEDGED alerts")
    past_count: int = Field(description="Count of PAST alerts")


class RiskAlertStatsResponse(BaseModel):
    """Response model for risk alert summary statistics.

    Attributes:
        total: Total number of alerts.
        by_status: Counts grouped by status (new, acknowledged, past).
        by_severity: Counts grouped by severity (warning, elevated, critical).
        by_type: Counts grouped by alert type (price_change, direction_disagreement, availability).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    total: int = Field(description="Total number of alerts")
    by_status: dict[str, int] = Field(description="Counts by status")
    by_severity: dict[str, int] = Field(description="Counts by severity")
    by_type: dict[str, int] = Field(description="Counts by alert type")


class AcknowledgeAlertRequest(BaseModel):
    """Request body for acknowledging or unacknowledging an alert.

    Attributes:
        acknowledged: Set to true to acknowledge, false to unacknowledge.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    acknowledged: bool = Field(description="Set to true to acknowledge alert")
