# Phase 105: Risk Monitoring Investigation & Discovery

**Completed:** 2026-02-19
**Status:** Ready for implementation

---

## Detection Algorithm Design

### Integration Point

The ideal integration point for alert detection is within `store_batch_results()` in `src/scraping/event_coordinator.py` (lines ~1567-1612), immediately after change detection and availability detection.

**Current Flow (lines 1467-1640):**
```
1. Build SnapshotWriteData DTOs from parsed results
2. Run classify_batch_changes() → identifies changed vs unchanged markets
3. Run _detect_and_log_availability_changes() → identifies market suspensions
4. Update cache with new snapshots
5. Enqueue write batch for persistence
```

**Proposed Flow with Alert Detection:**
```
1. Build SnapshotWriteData DTOs from parsed results
2. Run classify_batch_changes() → identifies changed vs unchanged markets
3. Run _detect_and_log_availability_changes() → identifies market suspensions
4. [NEW] Run detect_risk_alerts() → generates alerts from changes
   - Uses cached vs new market data
   - Calculates % changes for each outcome
   - Detects direction disagreement
   - Transforms availability changes to alerts
5. Update cache with new snapshots
6. [NEW] Enqueue alerts for WebSocket broadcast
7. Enqueue write batch for persistence (include alerts in batch)
```

**Why This Integration Point:**
- Access to both cached state (previous odds) and new state (just-scraped odds)
- Runs after change detection, so only processes changed markets (efficient)
- Near availability detection, can reuse its results
- Before cache update, so alerts reflect the transition state
- Near write queue, can batch alert persistence with snapshot writes

---

### Algorithm: Large % Change Detection

**Location:** New module `src/caching/risk_detection.py`

**Algorithm:**
```python
def calculate_outcome_change_percent(
    old_odds: float,
    new_odds: float
) -> float:
    """Calculate percentage change between odds values.

    Formula: ((new - old) / old) * 100
    Returns positive for increases, negative for decreases.
    """
    if old_odds == 0:
        return 0.0
    return ((new_odds - old_odds) / old_odds) * 100


def classify_severity(
    change_percent: float,
    threshold_warning: float = 7.0,
    threshold_elevated: float = 10.0,
    threshold_critical: float = 15.0,
) -> AlertSeverity | None:
    """Classify change magnitude into severity band.

    Returns:
        AlertSeverity.WARNING for 7-10% change
        AlertSeverity.ELEVATED for 10-15% change
        AlertSeverity.CRITICAL for 15%+ change
        None if below warning threshold
    """
    abs_change = abs(change_percent)
    if abs_change >= threshold_critical:
        return AlertSeverity.CRITICAL
    elif abs_change >= threshold_elevated:
        return AlertSeverity.ELEVATED
    elif abs_change >= threshold_warning:
        return AlertSeverity.WARNING
    return None


def detect_price_change_alerts(
    cached_markets: dict[tuple[str, float | None], CachedMarket],
    new_markets: list[MarketWriteData],
    event_id: int,
    bookmaker_slug: str,
    event_kickoff: datetime,
    thresholds: AlertThresholds,
    timestamp: datetime,
) -> list[RiskAlertData]:
    """Detect significant price changes between cached and new markets.

    For each market that exists in both cached and new state:
    1. Compare each outcome's odds
    2. Calculate % change
    3. If exceeds threshold, create alert

    Returns list of RiskAlertData DTOs for persistence.
    """
    alerts = []

    for market in new_markets:
        key = (market.betpawa_market_id, market.line)
        cached = cached_markets.get(key)
        if cached is None:
            continue  # New market, no comparison possible

        # Build outcome lookup from cached state
        cached_outcomes = {o["name"]: o["odds"] for o in cached.outcomes}

        for outcome in market.outcomes:
            outcome_name = outcome.get("name")
            new_odds = outcome.get("odds")
            old_odds = cached_outcomes.get(outcome_name)

            if old_odds is None or new_odds is None:
                continue

            change_pct = calculate_outcome_change_percent(old_odds, new_odds)
            severity = classify_severity(
                change_pct,
                thresholds.warning,
                thresholds.elevated,
                thresholds.critical,
            )

            if severity is not None:
                alerts.append(RiskAlertData(
                    event_id=event_id,
                    bookmaker_slug=bookmaker_slug,
                    market_id=market.betpawa_market_id,
                    market_name=market.betpawa_market_name,
                    line=market.line,
                    outcome_name=outcome_name,
                    alert_type=AlertType.PRICE_CHANGE,
                    severity=severity,
                    change_percent=change_pct,
                    old_value=old_odds,
                    new_value=new_odds,
                    competitor_direction=None,
                    detected_at=timestamp,
                    event_kickoff=event_kickoff,
                ))

    return alerts
```

---

### Algorithm: Direction Disagreement Detection

**Concept:** When Betpawa moves one direction and competitors move the opposite direction on the same market, this indicates potential pricing risk.

**Algorithm:**
```python
def get_movement_direction(old_odds: float, new_odds: float) -> str | None:
    """Determine if odds moved up, down, or stayed flat.

    Returns "up", "down", or None (no change / undefined).
    """
    if old_odds == 0 or new_odds == 0:
        return None
    diff = new_odds - old_odds
    if abs(diff) < 0.01:  # Within epsilon, consider unchanged
        return None
    return "up" if diff > 0 else "down"


def detect_direction_disagreement_alerts(
    betpawa_cached: dict[tuple[str, float | None], CachedMarket],
    betpawa_new: list[MarketWriteData],
    competitor_cached: dict[str, dict[tuple[str, float | None], CachedMarket]],
    competitor_new: dict[str, list[MarketWriteData]],
    event_id: int,
    event_kickoff: datetime,
    timestamp: datetime,
) -> list[RiskAlertData]:
    """Detect when Betpawa moves opposite to competitors.

    For each changed Betpawa market:
    1. Determine Betpawa's direction (up/down)
    2. For each competitor with same market, determine their direction
    3. If directions disagree, create alert

    Note: Only creates alert if BOTH sides have moved (not just one).
    """
    alerts = []

    for bp_market in betpawa_new:
        key = (bp_market.betpawa_market_id, bp_market.line)
        bp_cached = betpawa_cached.get(key)
        if bp_cached is None:
            continue

        # Check each outcome
        bp_cached_outcomes = {o["name"]: o["odds"] for o in bp_cached.outcomes}

        for outcome in bp_market.outcomes:
            outcome_name = outcome.get("name")
            bp_new_odds = outcome.get("odds")
            bp_old_odds = bp_cached_outcomes.get(outcome_name)

            if bp_old_odds is None or bp_new_odds is None:
                continue

            bp_direction = get_movement_direction(bp_old_odds, bp_new_odds)
            if bp_direction is None:
                continue  # Betpawa didn't move

            # Check each competitor
            for comp_slug, comp_markets in competitor_new.items():
                comp_cached_for_slug = competitor_cached.get(comp_slug, {})
                comp_market = next(
                    (m for m in comp_markets
                     if (m.betpawa_market_id, m.line) == key),
                    None
                )
                if comp_market is None:
                    continue

                comp_cached_market = comp_cached_for_slug.get(key)
                if comp_cached_market is None:
                    continue

                comp_cached_outcomes = {
                    o["name"]: o["odds"] for o in comp_cached_market.outcomes
                }
                comp_outcome = next(
                    (o for o in comp_market.outcomes if o.get("name") == outcome_name),
                    None
                )
                if comp_outcome is None:
                    continue

                comp_old_odds = comp_cached_outcomes.get(outcome_name)
                comp_new_odds = comp_outcome.get("odds")

                if comp_old_odds is None or comp_new_odds is None:
                    continue

                comp_direction = get_movement_direction(comp_old_odds, comp_new_odds)
                if comp_direction is None:
                    continue  # Competitor didn't move

                # Check for disagreement
                if bp_direction != comp_direction:
                    # Calculate the resulting gap
                    gap_pct = abs(
                        calculate_outcome_change_percent(bp_new_odds, comp_new_odds)
                    )

                    alerts.append(RiskAlertData(
                        event_id=event_id,
                        bookmaker_slug="betpawa",  # Alert is about Betpawa's position
                        market_id=bp_market.betpawa_market_id,
                        market_name=bp_market.betpawa_market_name,
                        line=bp_market.line,
                        outcome_name=outcome_name,
                        alert_type=AlertType.DIRECTION_DISAGREEMENT,
                        severity=AlertSeverity.ELEVATED,  # Always elevated for disagreement
                        change_percent=gap_pct,
                        old_value=bp_old_odds,
                        new_value=bp_new_odds,
                        competitor_direction=f"{comp_slug}:{comp_direction}",
                        detected_at=timestamp,
                        event_kickoff=event_kickoff,
                    ))

    return alerts
```

---

### Algorithm: Availability Alert Detection

**Concept:** Reuse the existing `_detect_and_log_availability_changes()` results to generate alerts when markets become unavailable or return.

**Algorithm:**
```python
def convert_availability_to_alerts(
    became_unavailable: list[CachedMarket],
    became_available: list[CachedMarket],
    event_id: int,
    bookmaker_slug: str,
    event_kickoff: datetime,
    timestamp: datetime,
) -> list[RiskAlertData]:
    """Convert availability changes to risk alerts.

    Availability changes are always WARNING severity:
    - Markets disappearing could indicate suspension for news
    - Markets returning could indicate updated information
    """
    alerts = []

    for market in became_unavailable:
        alerts.append(RiskAlertData(
            event_id=event_id,
            bookmaker_slug=bookmaker_slug,
            market_id=market.betpawa_market_id,
            market_name=market.betpawa_market_name,
            line=market.line,
            outcome_name=None,  # Applies to whole market
            alert_type=AlertType.AVAILABILITY,
            severity=AlertSeverity.WARNING,
            change_percent=0.0,  # N/A for availability
            old_value=None,  # N/A
            new_value=None,  # N/A
            competitor_direction="suspended",
            detected_at=timestamp,
            event_kickoff=event_kickoff,
        ))

    for market in became_available:
        alerts.append(RiskAlertData(
            event_id=event_id,
            bookmaker_slug=bookmaker_slug,
            market_id=market.betpawa_market_id,
            market_name=market.betpawa_market_name,
            line=market.line,
            outcome_name=None,
            alert_type=AlertType.AVAILABILITY,
            severity=AlertSeverity.WARNING,
            change_percent=0.0,
            old_value=None,
            new_value=None,
            competitor_direction="returned",
            detected_at=timestamp,
            event_kickoff=event_kickoff,
        ))

    return alerts
```

---

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCRAPE CYCLE (event_coordinator.py)                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Parse scrape results → SnapshotWriteData DTOs                       │
│     (bp_write_data, comp_write_data, event_id_map)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. classify_batch_changes(cache, bp_snapshots, comp_snapshots)         │
│     Returns: changed_bp, changed_comp, unchanged_bp_ids, unchanged_...  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. _detect_and_log_availability_changes(...)                           │
│     Returns: unavailable_bp, unavailable_comp, availability_stats       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  4. [NEW] detect_risk_alerts(                                           │
│       cache=odds_cache,                                                 │
│       changed_bp=changed_bp,                                            │
│       changed_comp=changed_comp,                                        │
│       unavailable_bp=unavailable_bp,                                    │
│       unavailable_comp=unavailable_comp,                                │
│       event_kickoffs=kickoff_by_sr,                                     │
│       thresholds=alert_thresholds,                                      │
│     )                                                                   │
│     Returns: list[RiskAlertData]                                        │
│                                                                         │
│     Internally calls:                                                   │
│     - detect_price_change_alerts() for each changed market              │
│     - detect_direction_disagreement_alerts() for BP vs competitors      │
│     - convert_availability_to_alerts() for availability changes         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌──────────────────────────────┐    ┌──────────────────────────────┐
│  5a. WebSocket broadcast      │    │  5b. Enqueue alerts for DB    │
│      ws_manager.broadcast(    │    │      write_queue.put(         │
│        "risk_alert",          │    │        WriteBatch(            │
│        alerts_payload         │    │          ...                  │
│      )                        │    │          alerts=alerts,       │
│                               │    │        )                      │
│  Real-time UI update          │    │      )                        │
└──────────────────────────────┘    └──────────────────────────────┘
                                                    │
                                                    ▼
                                    ┌──────────────────────────────┐
                                    │  6. write_handler persists    │
                                    │     INSERT INTO risk_alerts   │
                                    │     (batched with snapshots)  │
                                    └──────────────────────────────┘
```

---

## Database Schema Design

### RiskAlert Model

**Location:** New file `src/db/models/risk_alert.py`

```python
"""Risk alert model for odds movement detection.

This module defines the RiskAlert model for storing detected risk events
including significant price changes, direction disagreements between
bookmakers, and market availability changes.

Alerts support acknowledgment workflow and automatic status transitions
after event kickoff.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class AlertType(str, Enum):
    """Types of risk alerts detected by the system."""

    PRICE_CHANGE = "price_change"
    DIRECTION_DISAGREEMENT = "direction_disagreement"
    AVAILABILITY = "availability"


class AlertSeverity(str, Enum):
    """Severity classification for risk alerts."""

    WARNING = "warning"      # 7-10% change (yellow)
    ELEVATED = "elevated"    # 10-15% change (orange)
    CRITICAL = "critical"    # 15%+ change (red)


class AlertStatus(str, Enum):
    """Workflow status for risk alerts."""

    NEW = "new"                # Unacknowledged, pre-kickoff
    ACKNOWLEDGED = "acknowledged"  # User reviewed, pre-kickoff
    PAST = "past"              # Post-kickoff (automatic transition)


class RiskAlert(Base):
    """Detected risk event requiring monitoring attention.

    Records significant odds movements, direction disagreements between
    bookmakers, and market availability changes. Supports acknowledgment
    workflow and automatic post-kickoff status transitions.

    Attributes:
        id: Primary key (BigInteger for high volume).
        event_id: FK to events table.
        bookmaker_slug: Which bookmaker triggered the alert.
        market_id: Betpawa market ID affected.
        market_name: Human-readable market name.
        line: Line value for total/handicap markets (nullable).
        outcome_name: Specific outcome if applicable (nullable).
        alert_type: Type of alert (price_change, direction_disagreement, availability).
        severity: Severity level (warning, elevated, critical).
        change_percent: Absolute percentage change (0 for availability).
        old_value: Previous odds value (nullable for availability).
        new_value: Current odds value (nullable for availability).
        competitor_direction: For disagreement: "sportybet:up" format (nullable).
        detected_at: When the alert was detected.
        acknowledged_at: When user acknowledged (nullable).
        status: Current workflow status (new, acknowledged, past).
        event_kickoff: Kickoff time for automatic PAST transition.

    Relationships:
        event: Parent Event (many-to-one).

    Indexes:
        - idx_risk_alerts_event: (event_id, status) for event page badge queries
        - idx_risk_alerts_status_detected: (status, detected_at DESC) for Risk Monitoring page
        - idx_risk_alerts_kickoff: (event_kickoff) for auto-status background job
    """

    __tablename__ = "risk_alerts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    bookmaker_slug: Mapped[str] = mapped_column(String(50))
    market_id: Mapped[str] = mapped_column(String(50))
    market_name: Mapped[str] = mapped_column(String(255))
    line: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50))  # AlertType enum value
    severity: Mapped[str] = mapped_column(String(20))    # AlertSeverity enum value
    change_percent: Mapped[float] = mapped_column(Float, default=0.0)
    old_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitor_direction: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="new")  # AlertStatus enum value
    event_kickoff: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    event: Mapped["Event"] = relationship()

    __table_args__ = (
        # For event page badge queries: "count alerts for this event"
        Index("idx_risk_alerts_event", "event_id", "status"),
        # For Risk Monitoring page: "all NEW alerts, most recent first"
        Index(
            "idx_risk_alerts_status_detected",
            "status",
            "detected_at",
            postgresql_ops={"detected_at": "DESC"},
        ),
        # For auto-status job: "find alerts past kickoff"
        Index("idx_risk_alerts_kickoff", "event_kickoff"),
    )
```

---

### Settings Model Additions

**Location:** Update `src/db/models/settings.py`

```python
# Add these fields to the existing Settings class:

# Alert configuration (Phase 105)
alert_enabled: Mapped[bool] = mapped_column(default=True)
alert_threshold_warning: Mapped[float] = mapped_column(Float, default=7.0)
alert_threshold_elevated: Mapped[float] = mapped_column(Float, default=10.0)
alert_threshold_critical: Mapped[float] = mapped_column(Float, default=15.0)
alert_retention_days: Mapped[int] = mapped_column(default=7)
alert_lookback_minutes: Mapped[int] = mapped_column(default=60)
```

**Field Descriptions:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `alert_enabled` | bool | True | Master toggle for alert detection |
| `alert_threshold_warning` | float | 7.0 | % change threshold for WARNING severity |
| `alert_threshold_elevated` | float | 10.0 | % change threshold for ELEVATED severity |
| `alert_threshold_critical` | float | 15.0 | % change threshold for CRITICAL severity |
| `alert_retention_days` | int | 7 | Days to keep alerts (separate from odds retention) |
| `alert_lookback_minutes` | int | 60 | Comparison window for direction disagreement |

---

### Migration File

**Location:** `alembic/versions/XXXX_add_risk_alerts.py`

```python
"""Add risk_alerts table and settings columns.

Revision ID: XXXX
Revises: [previous]
Create Date: 2026-02-19
"""

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Create risk_alerts table
    op.create_table(
        "risk_alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("bookmaker_slug", sa.String(50), nullable=False),
        sa.Column("market_id", sa.String(50), nullable=False),
        sa.Column("market_name", sa.String(255), nullable=False),
        sa.Column("line", sa.Float(), nullable=True),
        sa.Column("outcome_name", sa.String(100), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("change_percent", sa.Float(), default=0.0),
        sa.Column("old_value", sa.Float(), nullable=True),
        sa.Column("new_value", sa.Float(), nullable=True),
        sa.Column("competitor_direction", sa.String(100), nullable=True),
        sa.Column("detected_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), default="new"),
        sa.Column("event_kickoff", sa.DateTime(), nullable=False),
    )

    # Create indexes
    op.create_index(
        "idx_risk_alerts_event",
        "risk_alerts",
        ["event_id", "status"],
    )
    op.create_index(
        "idx_risk_alerts_status_detected",
        "risk_alerts",
        ["status", sa.text("detected_at DESC")],
    )
    op.create_index(
        "idx_risk_alerts_kickoff",
        "risk_alerts",
        ["event_kickoff"],
    )

    # Add settings columns
    op.add_column("settings", sa.Column("alert_enabled", sa.Boolean(), default=True))
    op.add_column("settings", sa.Column("alert_threshold_warning", sa.Float(), default=7.0))
    op.add_column("settings", sa.Column("alert_threshold_elevated", sa.Float(), default=10.0))
    op.add_column("settings", sa.Column("alert_threshold_critical", sa.Float(), default=15.0))
    op.add_column("settings", sa.Column("alert_retention_days", sa.Integer(), default=7))
    op.add_column("settings", sa.Column("alert_lookback_minutes", sa.Integer(), default=60))


def downgrade() -> None:
    op.drop_index("idx_risk_alerts_kickoff")
    op.drop_index("idx_risk_alerts_status_detected")
    op.drop_index("idx_risk_alerts_event")
    op.drop_table("risk_alerts")

    op.drop_column("settings", "alert_enabled")
    op.drop_column("settings", "alert_threshold_warning")
    op.drop_column("settings", "alert_threshold_elevated")
    op.drop_column("settings", "alert_threshold_critical")
    op.drop_column("settings", "alert_retention_days")
    op.drop_column("settings", "alert_lookback_minutes")
```

---

### DTO for Alert Data

**Location:** Add to `src/storage/write_queue.py`

```python
@dataclass(frozen=True)
class RiskAlertData:
    """DTO for risk alert creation.

    Immutable data object passed from detection to write handler.
    Decouples detection logic from database persistence.
    """

    event_id: int
    bookmaker_slug: str
    market_id: str
    market_name: str
    line: float | None
    outcome_name: str | None
    alert_type: str  # AlertType enum value
    severity: str    # AlertSeverity enum value
    change_percent: float
    old_value: float | None
    new_value: float | None
    competitor_direction: str | None
    detected_at: datetime
    event_kickoff: datetime
```

---

## Implementation Phases

Based on this investigation, the following phases are confirmed:

1. **Phase 106: Backend Alert Detection** — Implement `src/caching/risk_detection.py` with all three detection algorithms, integrate into `event_coordinator.py`

2. **Phase 107: Alert Storage & API** — Run migration, implement write handler extension, create CRUD endpoints

3. **Phase 108: Risk Monitoring Page** — Build the main alerts table with tabs and filters

4. **Phase 109: Real-Time Updates** — WebSocket broadcast for new alerts, sidebar badge

5. **Phase 110: Cross-Page Integration** — Alert indicators on Odds Comparison and Event Details

6. **Phase 111: Settings & Configuration** — UI for threshold configuration

---

## Key Design Decisions

1. **Alert per outcome, not per market** — Each significant outcome change creates its own alert, enabling granular tracking

2. **Direction disagreement is always ELEVATED** — These are inherently concerning regardless of magnitude

3. **Availability alerts are WARNING severity** — They indicate change but not magnitude of risk

4. **Separate retention for alerts** — `alert_retention_days` independent from `odds_retention_days` since alerts may need longer visibility

5. **Status auto-transition via background job** — Post-kickoff events move to PAST automatically, not requiring manual action

6. **Detection in async path only** — Initial implementation focuses on scheduled scraping; on-demand scrapes can be added later

7. **BigInteger ID for volume** — Alerts table expected to grow large like odds_snapshots

---

*Investigation completed: 2026-02-19*
*Ready for Phase 106 implementation*
