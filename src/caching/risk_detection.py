"""Risk detection for odds movements, direction disagreements, and availability changes.

Identifies significant odds changes that warrant attention from risk monitors.
Detects three types of alerts:
    1. PRICE_CHANGE: Single bookmaker odds moved by >= threshold %
    2. DIRECTION_DISAGREEMENT: Betpawa moved opposite to competitor
    3. AVAILABILITY: Market became unavailable or returned

Integration point: Called from event_coordinator.store_batch_results() after
change detection and availability detection, before cache update.

Functions:
    calculate_outcome_change_percent(): % change between old/new odds
    classify_severity(): Map change % to severity band
    get_movement_direction(): Determine if odds went up/down
    detect_price_change_alerts(): Find significant price movements
    detect_direction_disagreement_alerts(): Find Betpawa vs competitor divergence
    convert_availability_to_alerts(): Transform availability changes to alerts
    detect_risk_alerts(): Main orchestrator calling all detection functions

Usage:
    alerts = detect_risk_alerts(
        cache=odds_cache,
        changed_bp=changed_bp,
        changed_comp=changed_comp,
        bp_write_data=bp_write_data,
        comp_write_data=comp_write_data,
        comp_meta=comp_meta,
        event_id_map=event_id_map,
        unavailable_bp=unavailable_bp,
        unavailable_comp=unavailable_comp,
        kickoff_by_sr=kickoff_by_sr,
        thresholds=AlertThresholds(7.0, 10.0, 15.0),
        timestamp=now,
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, NamedTuple

import structlog

if TYPE_CHECKING:
    from src.caching.odds_cache import CachedMarket, OddsCache
    from src.storage.write_queue import (
        MarketWriteData,
        RiskAlertData,
        SnapshotWriteData,
        CompetitorSnapshotWriteData,
        UnavailableMarketUpdate,
    )

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Threshold configuration
# ---------------------------------------------------------------------------


class AlertThresholds(NamedTuple):
    """Configurable threshold percentages for severity classification."""

    warning: float = 7.0
    elevated: float = 10.0
    critical: float = 15.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def calculate_outcome_change_percent(old_odds: float, new_odds: float) -> float:
    """Calculate percentage change between odds values.

    Formula: ((new - old) / old) * 100
    Returns positive for increases, negative for decreases.

    Parameters
    ----------
    old_odds:
        Previous odds value.
    new_odds:
        Current odds value.

    Returns
    -------
    float
        Percentage change (positive = increase, negative = decrease).
    """
    if old_odds == 0:
        return 0.0
    return ((new_odds - old_odds) / old_odds) * 100


def classify_severity(
    change_percent: float,
    thresholds: AlertThresholds,
) -> AlertSeverity | None:
    """Classify change magnitude into severity band.

    Parameters
    ----------
    change_percent:
        Percentage change (positive or negative).
    thresholds:
        AlertThresholds with warning, elevated, critical values.

    Returns
    -------
    AlertSeverity | None
        AlertSeverity.WARNING for warning-elevated % change
        AlertSeverity.ELEVATED for elevated-critical % change
        AlertSeverity.CRITICAL for critical+ % change
        None if below warning threshold
    """
    abs_change = abs(change_percent)
    if abs_change >= thresholds.critical:
        return AlertSeverity.CRITICAL
    elif abs_change >= thresholds.elevated:
        return AlertSeverity.ELEVATED
    elif abs_change >= thresholds.warning:
        return AlertSeverity.WARNING
    return None


def get_movement_direction(old_odds: float, new_odds: float) -> str | None:
    """Determine if odds moved up, down, or stayed flat.

    Parameters
    ----------
    old_odds:
        Previous odds value.
    new_odds:
        Current odds value.

    Returns
    -------
    str | None
        "up" if odds increased, "down" if decreased, None if unchanged/undefined.
    """
    if old_odds == 0 or new_odds == 0:
        return None
    diff = new_odds - old_odds
    if abs(diff) < 0.01:  # Within epsilon, consider unchanged
        return None
    return "up" if diff > 0 else "down"


# ---------------------------------------------------------------------------
# Detection functions
# ---------------------------------------------------------------------------


def detect_price_change_alerts(
    cached_markets: dict[tuple[str, float | None], Any],
    new_markets: tuple[Any, ...],
    event_id: int,
    bookmaker_slug: str,
    event_kickoff: datetime,
    thresholds: AlertThresholds,
    timestamp: datetime,
) -> list:
    """Detect significant price changes between cached and new markets.

    For each market that exists in both cached and new state:
    1. Compare each outcome's odds
    2. Calculate % change
    3. If exceeds threshold, create alert

    Parameters
    ----------
    cached_markets:
        Dict of (betpawa_market_id, line) -> CachedMarket from cache.
    new_markets:
        Tuple of MarketWriteData from current scrape.
    event_id:
        Event ID for the alert.
    bookmaker_slug:
        Bookmaker identifier (betpawa, sportybet, bet9ja).
    event_kickoff:
        Event kickoff time for alert context.
    thresholds:
        AlertThresholds for severity classification.
    timestamp:
        Detection timestamp.

    Returns
    -------
    list
        List of RiskAlertData DTOs for persistence.
    """
    from src.storage.write_queue import RiskAlertData

    alerts: list[RiskAlertData] = []

    for market in new_markets:
        key = (market.betpawa_market_id, market.line)
        cached = cached_markets.get(key)
        if cached is None:
            continue  # New market, no comparison possible

        # Build outcome lookup from cached state
        cached_outcomes = {o["name"]: o["odds"] for o in cached.outcomes}

        # Get outcomes from new market
        outcomes = market.outcomes if isinstance(market.outcomes, (list, dict)) else []
        if isinstance(outcomes, dict):
            outcomes = [outcomes]

        for outcome in outcomes:
            outcome_name = outcome.get("name")
            new_odds = outcome.get("odds")
            old_odds = cached_outcomes.get(outcome_name)

            if old_odds is None or new_odds is None:
                continue

            change_pct = calculate_outcome_change_percent(old_odds, new_odds)
            severity = classify_severity(change_pct, thresholds)

            if severity is not None:
                alerts.append(RiskAlertData(
                    event_id=event_id,
                    bookmaker_slug=bookmaker_slug,
                    market_id=market.betpawa_market_id,
                    market_name=market.betpawa_market_name,
                    line=market.line,
                    outcome_name=outcome_name,
                    alert_type=AlertType.PRICE_CHANGE.value,
                    severity=severity.value,
                    change_percent=change_pct,
                    old_value=old_odds,
                    new_value=new_odds,
                    competitor_old_value=None,
                    competitor_new_value=None,
                    competitor_direction=None,
                    detected_at=timestamp,
                    event_kickoff=event_kickoff,
                ))

    return alerts


def detect_direction_disagreement_alerts(
    cache: Any,
    changed_bp: list[tuple[int, int, list[Any]]],
    changed_comp: list[tuple[int, str, list[Any]]],
    bp_write_data: list[Any],
    comp_write_data: list[Any],
    comp_meta: list[tuple[str, str, int]],
    event_id_map: dict[str, int],
    kickoff_by_sr: dict[str, datetime],
    timestamp: datetime,
) -> list:
    """Detect when Betpawa moves opposite to competitors.

    For each changed Betpawa market:
    1. Determine Betpawa's direction (up/down)
    2. For each competitor with same market, determine their direction
    3. If directions disagree, create alert

    Note: Only creates alert if BOTH sides have moved (not just one).

    Parameters
    ----------
    cache:
        OddsCache instance for cached state lookup.
    changed_bp:
        Changed Betpawa snapshots from classify_batch_changes().
    changed_comp:
        Changed competitor snapshots from classify_batch_changes().
    bp_write_data:
        All Betpawa SnapshotWriteData from current scrape.
    comp_write_data:
        All competitor CompetitorSnapshotWriteData from current scrape.
    comp_meta:
        Metadata tuples (sr_id, source, comp_event_id) for competitors.
    event_id_map:
        SR ID -> event_id mapping.
    kickoff_by_sr:
        SR ID -> kickoff datetime mapping.
    timestamp:
        Detection timestamp.

    Returns
    -------
    list
        List of RiskAlertData DTOs for persistence.
    """
    from src.storage.write_queue import RiskAlertData

    alerts: list[RiskAlertData] = []

    # Build lookup for changed Betpawa markets: (event_id, market_id, line) -> market data
    bp_changed_markets: dict[tuple[int, str, float | None], tuple[Any, Any]] = {}
    for event_id, _bk_id, markets_data in changed_bp:
        # Find corresponding write data to get market details
        bp_data = next((b for b in bp_write_data if b.event_id == event_id), None)
        if bp_data is None:
            continue

        cached_bp = cache.get_betpawa_snapshot(event_id)
        if cached_bp is None:
            continue

        # Get cached markets for this bookmaker
        cached_snap = next(iter(cached_bp.values()), None) if cached_bp else None
        if cached_snap is None:
            continue

        cached_markets = {(m.betpawa_market_id, m.line): m for m in cached_snap.markets}

        for market in bp_data.markets:
            key = (event_id, market.betpawa_market_id, market.line)
            cached_m = cached_markets.get((market.betpawa_market_id, market.line))
            if cached_m:
                bp_changed_markets[key] = (cached_m, market)

    # Build lookup for competitor markets by event_id and source
    comp_by_event: dict[int, dict[str, tuple[Any, list[Any]]]] = {}
    for idx, cswd in enumerate(comp_write_data):
        sr_id, source, _comp_eid = comp_meta[idx]
        betpawa_eid = event_id_map.get(sr_id)
        if not betpawa_eid:
            continue

        if betpawa_eid not in comp_by_event:
            comp_by_event[betpawa_eid] = {}

        # Get cached competitor snapshot
        cached_comp = cache.get_competitor_snapshot(betpawa_eid)
        cached_snap = cached_comp.get(source) if cached_comp else None
        cached_markets = {(m.betpawa_market_id, m.line): m for m in cached_snap.markets} if cached_snap else {}

        comp_by_event[betpawa_eid][source] = (cached_markets, cswd.markets)

    # Now check for direction disagreements
    eid_to_sr: dict[int, str] = {v: k for k, v in event_id_map.items()}

    for (event_id, market_id, line), (bp_cached, bp_new) in bp_changed_markets.items():
        # Get kickoff for this event
        sr_id = eid_to_sr.get(event_id)
        kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
        if kickoff is None:
            continue

        # Build Betpawa outcome lookup
        bp_cached_outcomes = {o["name"]: o["odds"] for o in bp_cached.outcomes}

        bp_new_outcomes_raw = bp_new.outcomes if isinstance(bp_new.outcomes, (list, dict)) else []
        if isinstance(bp_new_outcomes_raw, dict):
            bp_new_outcomes_raw = [bp_new_outcomes_raw]

        for outcome in bp_new_outcomes_raw:
            outcome_name = outcome.get("name")
            bp_new_odds = outcome.get("odds")
            bp_old_odds = bp_cached_outcomes.get(outcome_name)

            if bp_old_odds is None or bp_new_odds is None:
                continue

            bp_direction = get_movement_direction(bp_old_odds, bp_new_odds)
            if bp_direction is None:
                continue  # Betpawa didn't move significantly

            # Check competitors for this event
            comp_data = comp_by_event.get(event_id, {})
            for comp_source, (cached_markets, new_markets) in comp_data.items():
                # Find matching market
                comp_cached = cached_markets.get((market_id, line))
                comp_new = next(
                    (m for m in new_markets if m.betpawa_market_id == market_id and m.line == line),
                    None
                )
                if comp_cached is None or comp_new is None:
                    continue

                comp_cached_outcomes = {o["name"]: o["odds"] for o in comp_cached.outcomes}

                comp_new_outcomes_raw = comp_new.outcomes if isinstance(comp_new.outcomes, (list, dict)) else []
                if isinstance(comp_new_outcomes_raw, dict):
                    comp_new_outcomes_raw = [comp_new_outcomes_raw]

                comp_outcome = next(
                    (o for o in comp_new_outcomes_raw if o.get("name") == outcome_name),
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
                    continue  # Competitor didn't move significantly

                # Check for disagreement
                if bp_direction != comp_direction:
                    # Calculate the resulting gap
                    gap_pct = abs(calculate_outcome_change_percent(bp_new_odds, comp_new_odds))

                    alerts.append(RiskAlertData(
                        event_id=event_id,
                        bookmaker_slug="betpawa",  # Alert is about Betpawa's position
                        market_id=market_id,
                        market_name=bp_new.betpawa_market_name,
                        line=line,
                        outcome_name=outcome_name,
                        alert_type=AlertType.DIRECTION_DISAGREEMENT.value,
                        severity=AlertSeverity.ELEVATED.value,  # Always elevated for disagreement
                        change_percent=gap_pct,
                        old_value=bp_old_odds,
                        new_value=bp_new_odds,
                        competitor_old_value=comp_old_odds,
                        competitor_new_value=comp_new_odds,
                        competitor_direction=f"{comp_source}:{comp_direction}",
                        detected_at=timestamp,
                        event_kickoff=kickoff,
                    ))

    return alerts


def convert_availability_to_alerts(
    unavailable_updates: tuple[Any, ...],
    bookmaker_slug: str,
    event_id_map: dict[str, int] | None,
    kickoff_by_sr: dict[str, datetime],
    timestamp: datetime,
    cache: Any,
) -> list:
    """Convert availability changes to risk alerts.

    Availability changes are always WARNING severity:
    - Markets disappearing could indicate suspension for news
    - Markets returning could indicate updated information

    Parameters
    ----------
    unavailable_updates:
        Tuple of UnavailableMarketUpdate DTOs.
    bookmaker_slug:
        Bookmaker identifier for alerts.
    event_id_map:
        SR ID -> event_id mapping (None for Betpawa).
    kickoff_by_sr:
        SR ID -> kickoff datetime mapping.
    timestamp:
        Detection timestamp.
    cache:
        OddsCache for looking up event info.

    Returns
    -------
    list
        List of RiskAlertData DTOs for persistence.
    """
    from src.storage.write_queue import RiskAlertData

    alerts: list[RiskAlertData] = []

    # Build reverse map for kickoff lookup
    eid_to_sr: dict[int, str] = {}
    if event_id_map:
        eid_to_sr = {v: k for k, v in event_id_map.items()}

    for update in unavailable_updates:
        # Get event_id from snapshot
        # Need to look up which event this snapshot belongs to
        event_id = None
        market_name = update.betpawa_market_id  # Default to ID if we can't find name

        # Try to find event_id from Betpawa cache (snapshot_id -> event_id)
        if bookmaker_slug == "betpawa":
            for eid, by_bk in cache._betpawa_snapshots.items():
                for _bk_id, snap in by_bk.items():
                    if snap.snapshot_id == update.snapshot_id:
                        event_id = eid
                        # Find market name
                        for m in snap.markets:
                            if m.betpawa_market_id == update.betpawa_market_id:
                                market_name = m.betpawa_market_name
                                break
                        break
                if event_id:
                    break
        else:
            # Competitor - look in competitor cache
            for eid, by_source in cache._competitor_snapshots.items():
                for source, snap in by_source.items():
                    if snap.snapshot_id == update.snapshot_id:
                        event_id = eid
                        for m in snap.markets:
                            if m.betpawa_market_id == update.betpawa_market_id:
                                market_name = m.betpawa_market_name
                                break
                        break
                if event_id:
                    break

        if event_id is None:
            continue

        # Get kickoff
        sr_id = eid_to_sr.get(event_id)
        kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
        if kickoff is None:
            # Skip if no kickoff available
            continue

        # Determine if became unavailable or returned
        direction = "suspended" if update.unavailable_at is not None else "returned"

        alerts.append(RiskAlertData(
            event_id=event_id,
            bookmaker_slug=bookmaker_slug,
            market_id=update.betpawa_market_id,
            market_name=market_name,
            line=None,  # Availability is at market level
            outcome_name=None,  # Applies to whole market
            alert_type=AlertType.AVAILABILITY.value,
            severity=AlertSeverity.WARNING.value,
            change_percent=0.0,  # N/A for availability
            old_value=None,  # N/A
            new_value=None,  # N/A
            competitor_old_value=None,
            competitor_new_value=None,
            competitor_direction=direction,
            detected_at=timestamp,
            event_kickoff=kickoff,
        ))

    return alerts


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def detect_risk_alerts(
    cache: Any,
    changed_bp: list[tuple[int, int, list[Any]]],
    changed_comp: list[tuple[int, str, list[Any]]],
    bp_write_data: list[Any],
    comp_write_data: list[Any],
    comp_meta: list[tuple[str, str, int]],
    event_id_map: dict[str, int],
    unavailable_bp: tuple[Any, ...],
    unavailable_comp: tuple[Any, ...],
    kickoff_by_sr: dict[str, datetime],
    thresholds: AlertThresholds,
    timestamp: datetime,
) -> list:
    """Orchestrate all risk detection algorithms.

    Calls:
    1. detect_price_change_alerts() for Betpawa price changes
    2. detect_price_change_alerts() for competitor price changes
    3. detect_direction_disagreement_alerts() for Betpawa vs competitor divergence
    4. convert_availability_to_alerts() for Betpawa availability changes
    5. convert_availability_to_alerts() for competitor availability changes

    Parameters
    ----------
    cache:
        OddsCache instance holding current cached data.
    changed_bp:
        Changed Betpawa snapshots from classify_batch_changes().
    changed_comp:
        Changed competitor snapshots from classify_batch_changes().
    bp_write_data:
        All Betpawa SnapshotWriteData from current scrape.
    comp_write_data:
        All competitor CompetitorSnapshotWriteData from current scrape.
    comp_meta:
        Metadata tuples (sr_id, source, comp_event_id) for competitors.
    event_id_map:
        SR ID -> event_id mapping.
    unavailable_bp:
        Betpawa UnavailableMarketUpdate tuples.
    unavailable_comp:
        Competitor UnavailableMarketUpdate tuples.
    kickoff_by_sr:
        SR ID -> kickoff datetime mapping.
    thresholds:
        AlertThresholds for severity classification.
    timestamp:
        Detection timestamp.

    Returns
    -------
    list
        Combined list of RiskAlertData DTOs from all detection algorithms.
    """
    all_alerts: list = []

    # Build reverse map for kickoff lookup
    eid_to_sr: dict[int, str] = {v: k for k, v in event_id_map.items()}

    # Build set of matched market keys per event (markets that exist on competitors)
    # Only generate alerts for markets that have competitor coverage
    matched_markets_by_event: dict[int, set[tuple[str, float | None]]] = {}
    for idx, cswd in enumerate(comp_write_data):
        sr_id, _source, _comp_eid = comp_meta[idx]
        event_id = event_id_map.get(sr_id)
        if event_id is None:
            continue
        if event_id not in matched_markets_by_event:
            matched_markets_by_event[event_id] = set()
        for market in cswd.markets:
            matched_markets_by_event[event_id].add((market.betpawa_market_id, market.line))

    # 1. Betpawa price change alerts (only for matched markets)
    for event_id, bk_id, markets_data in changed_bp:
        # Get cached markets for comparison
        cached_bp = cache.get_betpawa_snapshot(event_id)
        if cached_bp is None:
            continue

        cached_snap = cached_bp.get(bk_id)
        if cached_snap is None:
            continue

        cached_markets = {(m.betpawa_market_id, m.line): m for m in cached_snap.markets}

        # Get corresponding write data for new market details
        bp_data = next((b for b in bp_write_data if b.event_id == event_id and b.bookmaker_id == bk_id), None)
        if bp_data is None:
            continue

        # Get kickoff
        sr_id = eid_to_sr.get(event_id)
        kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
        if kickoff is None:
            continue

        # Get matched markets for this event
        matched = matched_markets_by_event.get(event_id, set())

        alerts = detect_price_change_alerts(
            cached_markets=cached_markets,
            new_markets=bp_data.markets,
            event_id=event_id,
            bookmaker_slug="betpawa",
            event_kickoff=kickoff,
            thresholds=thresholds,
            timestamp=timestamp,
        )
        # Filter to only matched markets (markets with competitor coverage)
        matched_alerts = [
            a for a in alerts
            if (a.market_id, a.line) in matched
        ]
        all_alerts.extend(matched_alerts)

    # 2. Competitor price change alerts (inherently matched)
    for betpawa_eid, source, markets_data in changed_comp:
        # Get cached markets for comparison
        cached_comp = cache.get_competitor_snapshot(betpawa_eid)
        if cached_comp is None:
            continue

        cached_snap = cached_comp.get(source)
        if cached_snap is None:
            continue

        cached_markets = {(m.betpawa_market_id, m.line): m for m in cached_snap.markets}

        # Find corresponding write data
        comp_data = None
        for idx, cswd in enumerate(comp_write_data):
            sr_id, src, _comp_eid = comp_meta[idx]
            if event_id_map.get(sr_id) == betpawa_eid and src == source:
                comp_data = cswd
                break

        if comp_data is None:
            continue

        # Get kickoff
        sr_id = eid_to_sr.get(betpawa_eid)
        kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
        if kickoff is None:
            continue

        alerts = detect_price_change_alerts(
            cached_markets=cached_markets,
            new_markets=comp_data.markets,
            event_id=betpawa_eid,
            bookmaker_slug=source,
            event_kickoff=kickoff,
            thresholds=thresholds,
            timestamp=timestamp,
        )
        all_alerts.extend(alerts)

    # 3. Direction disagreement alerts
    direction_alerts = detect_direction_disagreement_alerts(
        cache=cache,
        changed_bp=changed_bp,
        changed_comp=changed_comp,
        bp_write_data=bp_write_data,
        comp_write_data=comp_write_data,
        comp_meta=comp_meta,
        event_id_map=event_id_map,
        kickoff_by_sr=kickoff_by_sr,
        timestamp=timestamp,
    )
    all_alerts.extend(direction_alerts)

    # 4. Betpawa availability alerts (filtered to matched markets)
    if unavailable_bp:
        bp_avail_alerts = convert_availability_to_alerts(
            unavailable_updates=unavailable_bp,
            bookmaker_slug="betpawa",
            event_id_map=event_id_map,
            kickoff_by_sr=kickoff_by_sr,
            timestamp=timestamp,
            cache=cache,
        )
        # Filter to matched markets only
        matched_avail_alerts = [
            a for a in bp_avail_alerts
            if (a.market_id, a.line) in matched_markets_by_event.get(a.event_id, set())
        ]
        all_alerts.extend(matched_avail_alerts)

    # 5. Competitor availability alerts
    if unavailable_comp:
        # Group by source for proper bookmaker_slug
        comp_by_snapshot: dict[int, str] = {}
        for idx, cswd in enumerate(comp_write_data):
            _sr_id, source, _comp_eid = comp_meta[idx]
            # Map snapshot_id to source - need to track this during processing
            # For now, iterate through each source
            pass

        # For simplicity, we'll create alerts with generic handling
        for update in unavailable_comp:
            # Find the source for this snapshot
            source = None
            event_id = None
            market_name = update.betpawa_market_id

            for eid, by_source in cache._competitor_snapshots.items():
                for src, snap in by_source.items():
                    if snap.snapshot_id == update.snapshot_id:
                        source = src
                        event_id = eid
                        for m in snap.markets:
                            if m.betpawa_market_id == update.betpawa_market_id:
                                market_name = m.betpawa_market_name
                                break
                        break
                if source:
                    break

            if source is None or event_id is None:
                continue

            sr_id = eid_to_sr.get(event_id)
            kickoff = kickoff_by_sr.get(sr_id) if sr_id else None
            if kickoff is None:
                continue

            direction = "suspended" if update.unavailable_at is not None else "returned"

            from src.storage.write_queue import RiskAlertData
            all_alerts.append(RiskAlertData(
                event_id=event_id,
                bookmaker_slug=source,
                market_id=update.betpawa_market_id,
                market_name=market_name,
                line=None,
                outcome_name=None,
                alert_type=AlertType.AVAILABILITY.value,
                severity=AlertSeverity.WARNING.value,
                change_percent=0.0,
                old_value=None,
                new_value=None,
                competitor_old_value=None,
                competitor_new_value=None,
                competitor_direction=direction,
                detected_at=timestamp,
                event_kickoff=kickoff,
            ))

    logger.debug(
        "risk_detection.complete",
        total_alerts=len(all_alerts),
        price_change=sum(1 for a in all_alerts if a.alert_type == AlertType.PRICE_CHANGE.value),
        direction=sum(1 for a in all_alerts if a.alert_type == AlertType.DIRECTION_DISAGREEMENT.value),
        availability=sum(1 for a in all_alerts if a.alert_type == AlertType.AVAILABILITY.value),
    )

    return all_alerts
