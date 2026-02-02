"""Market Mapping Audit Script.

Comprehensive audit of market mapping across all 3 bookmakers to identify
all unmapped and incorrectly mapped markets.

Usage:
    python -m src.scripts.audit_market_mapping [--output-dir=PATH]
"""

import asyncio
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.engine import async_session_factory
from src.db.models import (
    CompetitorEvent,
    CompetitorOddsSnapshot,
    CompetitorSource,
    CompetitorTournament,
    Event,
    OddsSnapshot,
)
from src.market_mapping.mappers.bet9ja import map_bet9ja_market_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.sportybet import SportybetMarket
from src.market_mapping.utils import parse_bet9ja_key

# Import MappingError from the non-src path to match what mappers use
from market_mapping.types.errors import MappingError, MappingErrorCode


@dataclass
class MappingErrorRecord:
    """Record of a mapping failure."""

    platform: str
    error_code: str
    market_id: str
    market_desc: str | None
    param: str | None
    context: dict[str, Any]
    event_id: int
    count: int = 1


@dataclass
class AuditStats:
    """Statistics for the audit."""

    # Events
    total_events_analyzed: int = 0
    events_with_betpawa: int = 0
    events_with_sportybet: int = 0
    events_with_bet9ja: int = 0
    events_with_all_platforms: int = 0

    # Unique tournaments/leagues
    unique_tournaments: set = field(default_factory=set)
    unique_countries: set = field(default_factory=set)

    # SportyBet stats
    sportybet_total_markets: int = 0
    sportybet_mapped: int = 0
    sportybet_failed: int = 0
    sportybet_errors_by_code: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Bet9ja stats
    bet9ja_total_markets: int = 0
    bet9ja_mapped: int = 0
    bet9ja_failed: int = 0
    bet9ja_errors_by_code: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # BetPawa stats (for reference)
    betpawa_total_markets: int = 0


@dataclass
class UnmappedMarket:
    """Aggregated info about an unmapped market."""

    platform: str
    market_id: str
    market_desc: str | None
    error_code: str
    frequency: int = 1
    sample_context: dict | None = None
    event_ids: list[int] = field(default_factory=list)


def categorize_market(market_desc: str | None, market_id: str) -> str:
    """Infer market category from description or ID."""
    if not market_desc:
        market_desc = ""

    desc_lower = market_desc.lower()
    id_lower = market_id.lower()
    combined = f"{desc_lower} {id_lower}"

    # Category detection based on keywords
    if any(kw in combined for kw in ["corner", "cornr"]):
        return "Corners"
    if any(kw in combined for kw in ["card", "book", "yellow", "red", "send"]):
        return "Cards/Bookings"
    if any(kw in combined for kw in ["player", "scorer", "goalscorer", "anytime"]):
        return "Player Props"
    if any(kw in combined for kw in ["penalty", "pk"]):
        return "Penalties"
    if any(kw in combined for kw in ["1x2", "result", "winner"]):
        return "Match Result"
    if any(kw in combined for kw in ["over", "under", "o/u", "total"]):
        return "Over/Under"
    if any(kw in combined for kw in ["handicap", "hcp", "spread"]):
        return "Handicaps"
    if any(kw in combined for kw in ["btts", "gg", "ng", "both team"]):
        return "BTTS"
    if any(kw in combined for kw in ["half", "1h", "2h", "ht", "ft"]):
        return "Half-Based"
    if any(kw in combined for kw in ["correct score", "exact", "cs"]):
        return "Correct Score"
    if any(kw in combined for kw in ["odd", "even"]):
        return "Odd/Even"
    if any(kw in combined for kw in ["goal", "score"]):
        return "Goals"
    if any(kw in combined for kw in ["multi", "combo"]):
        return "Combo Markets"
    if any(kw in combined for kw in ["special", "custom"]):
        return "Specials"
    if any(kw in combined for kw in ["minute", "time"]):
        return "Time-Based"
    if any(kw in combined for kw in ["draw no bet", "dnb"]):
        return "Draw No Bet"
    if any(kw in combined for kw in ["double chance", "dc"]):
        return "Double Chance"
    if any(kw in combined for kw in ["margin", "winning"]):
        return "Winning Margin"

    return "Uncategorized"


async def fetch_diverse_events(session: AsyncSession, min_events: int = 50) -> list[dict]:
    """Fetch diverse events with good coverage across platforms.

    Prioritizes:
    - Events with data from all 3 platforms or at least 2
    - Different tournaments, leagues, countries
    """
    print(f"Fetching at least {min_events} diverse events...")

    # First, find BetPawa events that have corresponding competitor events
    # Get BetPawa events with recent snapshots
    betpawa_query = (
        select(Event)
        .join(OddsSnapshot, Event.id == OddsSnapshot.event_id)
        .where(OddsSnapshot.raw_response.isnot(None))
        .options(selectinload(Event.tournament))
        .distinct()
        .limit(200)
    )

    result = await session.execute(betpawa_query)
    betpawa_events = result.scalars().unique().all()

    print(f"  Found {len(betpawa_events)} BetPawa events with raw snapshots")

    collected_events = []
    tournament_counts = Counter()
    country_counts = Counter()

    for event in betpawa_events:
        sr_id = event.sportradar_id

        # Find corresponding competitor events
        sportybet_query = (
            select(CompetitorEvent)
            .where(
                CompetitorEvent.source == CompetitorSource.SPORTYBET,
                CompetitorEvent.sportradar_id == sr_id,
            )
            .options(selectinload(CompetitorEvent.odds_snapshots))
        )
        bet9ja_query = (
            select(CompetitorEvent)
            .where(
                CompetitorEvent.source == CompetitorSource.BET9JA,
                CompetitorEvent.sportradar_id == sr_id,
            )
            .options(selectinload(CompetitorEvent.odds_snapshots))
        )

        sportybet_result = await session.execute(sportybet_query)
        bet9ja_result = await session.execute(bet9ja_query)

        sportybet_event = sportybet_result.scalar_one_or_none()
        bet9ja_event = bet9ja_result.scalar_one_or_none()

        # Only include events with at least 2 platforms
        platform_count = 1  # BetPawa
        if sportybet_event and sportybet_event.odds_snapshots:
            has_sportybet_data = any(s.raw_response for s in sportybet_event.odds_snapshots)
            if has_sportybet_data:
                platform_count += 1
        else:
            has_sportybet_data = False

        if bet9ja_event and bet9ja_event.odds_snapshots:
            has_bet9ja_data = any(s.raw_response for s in bet9ja_event.odds_snapshots)
            if has_bet9ja_data:
                platform_count += 1
        else:
            has_bet9ja_data = False

        if platform_count < 2:
            continue

        # Get tournament and country for diversity tracking
        tournament_name = event.tournament.name if event.tournament else "Unknown"
        country = event.tournament.country if event.tournament else "Unknown"

        # Skip if we have too many from this tournament (for diversity)
        if tournament_counts[tournament_name] >= 5 and len(collected_events) < min_events:
            # Allow more if we're still below minimum
            if tournament_counts[tournament_name] >= 10:
                continue

        # Get raw snapshots
        betpawa_snapshot_query = (
            select(OddsSnapshot)
            .where(
                OddsSnapshot.event_id == event.id,
                OddsSnapshot.raw_response.isnot(None),
            )
            .order_by(OddsSnapshot.captured_at.desc())
            .limit(1)
        )
        bp_result = await session.execute(betpawa_snapshot_query)
        betpawa_snapshot = bp_result.scalar_one_or_none()

        collected_events.append({
            "event_id": event.id,
            "sportradar_id": sr_id,
            "name": event.name,
            "home_team": event.home_team,
            "away_team": event.away_team,
            "tournament": tournament_name,
            "country": country,
            "kickoff": event.kickoff.isoformat() if event.kickoff else None,
            "platforms": {
                "betpawa": {
                    "has_data": True,
                    "raw_response": betpawa_snapshot.raw_response if betpawa_snapshot else None,
                },
                "sportybet": {
                    "has_data": has_sportybet_data,
                    "competitor_event_id": sportybet_event.id if sportybet_event else None,
                    "raw_response": next(
                        (s.raw_response for s in sportybet_event.odds_snapshots if s.raw_response),
                        None
                    ) if sportybet_event and sportybet_event.odds_snapshots else None,
                },
                "bet9ja": {
                    "has_data": has_bet9ja_data,
                    "competitor_event_id": bet9ja_event.id if bet9ja_event else None,
                    "raw_response": next(
                        (s.raw_response for s in bet9ja_event.odds_snapshots if s.raw_response),
                        None
                    ) if bet9ja_event and bet9ja_event.odds_snapshots else None,
                },
            },
            "platform_count": platform_count,
        })

        tournament_counts[tournament_name] += 1
        country_counts[country] += 1

        if len(collected_events) >= min_events * 2:  # Collect extra for diversity
            break

    # Sort by platform coverage (3 platforms first) and diversity
    collected_events.sort(key=lambda e: (-e["platform_count"], e["tournament"]))

    # Return the minimum requested, prioritizing diverse coverage
    final_events = collected_events[:max(min_events, len(collected_events))]

    print(f"  Collected {len(final_events)} events")
    print(f"  Unique tournaments: {len(tournament_counts)}")
    print(f"  Unique countries: {len(country_counts)}")

    return final_events


def extract_sportybet_markets(raw_response: dict | None) -> list[SportybetMarket]:
    """Extract SportyBet markets from raw response."""
    if not raw_response:
        return []

    markets = []

    # SportyBet structure: {"data": {"markets": [...]}} or {"markets": [...]}
    if "data" in raw_response and isinstance(raw_response["data"], dict):
        raw_markets = raw_response["data"].get("markets", [])
    elif "markets" in raw_response:
        raw_markets = raw_response.get("markets", [])
    else:
        raw_markets = []

    for m in raw_markets:
        try:
            market = SportybetMarket.model_validate(m)
            markets.append(market)
        except Exception:
            # Skip invalid markets
            continue

    return markets


def extract_bet9ja_markets(raw_response: dict | None) -> list[dict]:
    """Extract Bet9ja markets from raw response.

    Returns list of dicts with: market_key, param, outcomes (dict)
    Bet9ja uses flattened key format: S_MARKET[@PARAM]_OUTCOME
    The odds are stored in the 'O' field of the raw response.
    """
    if not raw_response:
        return []

    # Bet9ja stores odds in the 'O' key
    odds_data = raw_response.get("O", {})
    if not isinstance(odds_data, dict):
        return []

    # Group by market+param
    market_groups: dict[tuple[str, str | None], dict[str, str]] = {}

    for key, value in odds_data.items():
        if not key.startswith("S_"):
            continue

        parsed = parse_bet9ja_key(key)
        if not parsed:
            continue

        group_key = (parsed.market, parsed.param)
        if group_key not in market_groups:
            market_groups[group_key] = {}
        # Convert value to string for consistent handling
        market_groups[group_key][parsed.outcome] = str(value)

    return [
        {
            "market_key": market,
            "param": param,
            "outcomes": outcomes,
        }
        for (market, param), outcomes in market_groups.items()
    ]


def analyze_sportybet_mapping(
    markets: list[SportybetMarket],
    event_id: int,
    stats: AuditStats,
    unmapped_tracker: dict[tuple[str, str], UnmappedMarket],
) -> list[MappingErrorRecord]:
    """Analyze SportyBet market mapping and capture errors."""
    errors = []

    for market in markets:
        stats.sportybet_total_markets += 1

        try:
            mapped = map_sportybet_to_betpawa(market)
            stats.sportybet_mapped += 1
        except MappingError as e:
            stats.sportybet_failed += 1
            stats.sportybet_errors_by_code[e.code] += 1

            # Create error record
            error_record = MappingErrorRecord(
                platform="sportybet",
                error_code=str(e.code),
                market_id=market.id,
                market_desc=market.desc,
                param=market.specifier,
                context=e.context or {},
                event_id=event_id,
            )
            errors.append(error_record)

            # Track unique unmapped markets
            key = ("sportybet", market.id)
            if key not in unmapped_tracker:
                unmapped_tracker[key] = UnmappedMarket(
                    platform="sportybet",
                    market_id=market.id,
                    market_desc=market.desc,
                    error_code=str(e.code),
                    sample_context=e.context,
                    event_ids=[event_id],
                )
            else:
                unmapped_tracker[key].frequency += 1
                if event_id not in unmapped_tracker[key].event_ids:
                    unmapped_tracker[key].event_ids.append(event_id)

    return errors


def analyze_bet9ja_mapping(
    markets: list[dict],
    event_id: int,
    stats: AuditStats,
    unmapped_tracker: dict[tuple[str, str], UnmappedMarket],
) -> list[MappingErrorRecord]:
    """Analyze Bet9ja market mapping and capture errors."""
    errors = []

    for market in markets:
        stats.bet9ja_total_markets += 1
        market_key = market["market_key"]
        param = market["param"]
        outcomes = market["outcomes"]

        try:
            mapped = map_bet9ja_market_to_betpawa(market_key, param, outcomes)
            stats.bet9ja_mapped += 1
        except MappingError as e:
            stats.bet9ja_failed += 1
            stats.bet9ja_errors_by_code[e.code] += 1

            # Create error record
            error_record = MappingErrorRecord(
                platform="bet9ja",
                error_code=str(e.code),
                market_id=market_key,
                market_desc=None,  # Bet9ja doesn't have market descriptions in same format
                param=param,
                context=e.context or {},
                event_id=event_id,
            )
            errors.append(error_record)

            # Track unique unmapped markets
            key = ("bet9ja", market_key)
            if key not in unmapped_tracker:
                unmapped_tracker[key] = UnmappedMarket(
                    platform="bet9ja",
                    market_id=market_key,
                    market_desc=None,
                    error_code=str(e.code),
                    sample_context=e.context,
                    event_ids=[event_id],
                )
            else:
                unmapped_tracker[key].frequency += 1
                if event_id not in unmapped_tracker[key].event_ids:
                    unmapped_tracker[key].event_ids.append(event_id)

    return errors


def count_betpawa_markets(raw_response: dict | None) -> int:
    """Count BetPawa markets from raw response."""
    if not raw_response:
        return 0

    # BetPawa structure: {"markets": [...]} where each market has outcomes
    markets = raw_response.get("markets", [])
    return len(markets)


def generate_audit_report(
    stats: AuditStats,
    unmapped_tracker: dict[tuple[str, str], UnmappedMarket],
    output_path: Path,
) -> str:
    """Generate the audit findings report as markdown."""

    # Calculate success rates
    sportybet_rate = (
        (stats.sportybet_mapped / stats.sportybet_total_markets * 100)
        if stats.sportybet_total_markets > 0 else 0
    )
    bet9ja_rate = (
        (stats.bet9ja_mapped / stats.bet9ja_total_markets * 100)
        if stats.bet9ja_total_markets > 0 else 0
    )

    # Group unmapped by category
    categories: dict[str, list[UnmappedMarket]] = defaultdict(list)
    for (platform, market_id), unmapped in unmapped_tracker.items():
        category = categorize_market(unmapped.market_desc, market_id)
        categories[category].append(unmapped)

    # Sort categories by total frequency
    sorted_categories = sorted(
        categories.items(),
        key=lambda x: sum(m.frequency for m in x[1]),
        reverse=True,
    )

    # Generate report
    report_lines = [
        "# Market Mapping Audit Findings",
        "",
        f"*Generated: {datetime.now().isoformat()}*",
        "",
        "## Executive Summary",
        "",
        f"- **Total events analyzed:** {stats.total_events_analyzed}",
        f"- **Events with all 3 platforms:** {stats.events_with_all_platforms}",
        f"- **Unique tournaments:** {len(stats.unique_tournaments)}",
        f"- **Unique countries:** {len(stats.unique_countries)}",
        "",
        "### Platform Coverage",
        "",
        "| Platform | Total Markets | Mapped | Failed | Success Rate |",
        "|----------|--------------|--------|--------|--------------|",
        f"| SportyBet | {stats.sportybet_total_markets} | {stats.sportybet_mapped} | {stats.sportybet_failed} | {sportybet_rate:.1f}% |",
        f"| Bet9ja | {stats.bet9ja_total_markets} | {stats.bet9ja_mapped} | {stats.bet9ja_failed} | {bet9ja_rate:.1f}% |",
        f"| BetPawa (reference) | {stats.betpawa_total_markets} | - | - | - |",
        "",
        f"**Unique unmapped market types:** {len(unmapped_tracker)}",
        "",
        "## Error Code Breakdown",
        "",
        "### SportyBet Errors by Code",
        "",
        "| Error Code | Count |",
        "|------------|-------|",
    ]

    for code, count in sorted(stats.sportybet_errors_by_code.items(), key=lambda x: -x[1]):
        report_lines.append(f"| {code} | {count} |")

    report_lines.extend([
        "",
        "### Bet9ja Errors by Code",
        "",
        "| Error Code | Count |",
        "|------------|-------|",
    ])

    for code, count in sorted(stats.bet9ja_errors_by_code.items(), key=lambda x: -x[1]):
        report_lines.append(f"| {code} | {count} |")

    report_lines.extend([
        "",
        "## Unmapped Markets by Category",
        "",
        "Markets grouped by inferred category, sorted by total frequency (impact).",
        "",
    ])

    for category, markets in sorted_categories:
        total_freq = sum(m.frequency for m in markets)
        report_lines.extend([
            f"### {category}",
            "",
            f"**Total unmapped occurrences:** {total_freq}",
            "",
            "| Platform | Market ID | Description | Frequency | Error Code | Priority |",
            "|----------|-----------|-------------|-----------|------------|----------|",
        ])

        # Sort markets within category by frequency
        for market in sorted(markets, key=lambda m: -m.frequency):
            # Determine priority based on frequency
            if market.frequency >= 30:
                priority = "HIGH"
            elif market.frequency >= 10:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            desc = market.market_desc or "-"
            # Truncate long descriptions
            if len(desc) > 50:
                desc = desc[:47] + "..."

            report_lines.append(
                f"| {market.platform} | `{market.market_id}` | {desc} | {market.frequency} | {market.error_code} | {priority} |"
            )

        report_lines.append("")

    # Prioritized recommendations
    report_lines.extend([
        "## Prioritized Fix Recommendations",
        "",
        "Based on frequency and cross-platform availability:",
        "",
    ])

    # Get high-impact unmapped markets
    high_impact = [
        m for m in unmapped_tracker.values()
        if m.frequency >= 10
    ]
    high_impact.sort(key=lambda m: -m.frequency)

    for i, market in enumerate(high_impact[:20], 1):
        category = categorize_market(market.market_desc, market.market_id)
        report_lines.append(
            f"{i}. **{market.market_id}** ({market.platform}) - {category}: "
            f"Appears in {market.frequency} events. Error: `{market.error_code}`"
        )

    if not high_impact:
        report_lines.append("*No high-impact unmapped markets found (frequency >= 10)*")

    report_lines.extend([
        "",
        "## Next Steps",
        "",
        "1. Add mappings for HIGH priority markets first",
        "2. Consider whether LOW priority markets are platform-specific (not worth mapping)",
        "3. Review UNKNOWN_MARKET errors - may indicate new markets added by competitors",
        "4. Review NO_MATCHING_OUTCOMES errors - may indicate outcome structure mismatches",
        "",
        "---",
        "",
        "*This report was auto-generated by the market mapping audit script.*",
    ])

    report_content = "\n".join(report_lines)

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content, encoding="utf-8")

    return report_content


async def run_audit(min_events: int = 50, output_dir: Path | None = None) -> tuple[AuditStats, str]:
    """Run the complete market mapping audit."""

    if output_dir is None:
        # Go from src/scripts/ to root, then to .planning/
        output_dir = Path(__file__).parent.parent.parent / ".planning" / "phases" / "43-market-mapping-audit"

    print("=" * 60)
    print("MARKET MAPPING AUDIT")
    print("=" * 60)
    print()

    stats = AuditStats()
    unmapped_tracker: dict[tuple[str, str], UnmappedMarket] = {}
    all_errors: list[MappingErrorRecord] = []

    async with async_session_factory() as session:
        # Task 1: Fetch diverse events with raw market data
        print("TASK 1: Fetching diverse events with raw market data...")
        events = await fetch_diverse_events(session, min_events)

        stats.total_events_analyzed = len(events)

        # Task 2: Analyze mapping for each event
        print()
        print("TASK 2: Running mapping analysis...")
        print()

        for i, event in enumerate(events, 1):
            event_id = event["event_id"]
            platforms = event["platforms"]

            # Track platform coverage
            stats.unique_tournaments.add(event.get("tournament", "Unknown"))
            stats.unique_countries.add(event.get("country", "Unknown"))

            has_betpawa = platforms["betpawa"]["has_data"]
            has_sportybet = platforms["sportybet"]["has_data"]
            has_bet9ja = platforms["bet9ja"]["has_data"]

            if has_betpawa:
                stats.events_with_betpawa += 1
            if has_sportybet:
                stats.events_with_sportybet += 1
            if has_bet9ja:
                stats.events_with_bet9ja += 1
            if has_betpawa and has_sportybet and has_bet9ja:
                stats.events_with_all_platforms += 1

            # Count BetPawa markets for reference
            if has_betpawa and platforms["betpawa"]["raw_response"]:
                stats.betpawa_total_markets += count_betpawa_markets(
                    platforms["betpawa"]["raw_response"]
                )

            # Analyze SportyBet
            if has_sportybet and platforms["sportybet"]["raw_response"]:
                sportybet_markets = extract_sportybet_markets(
                    platforms["sportybet"]["raw_response"]
                )
                errors = analyze_sportybet_mapping(
                    sportybet_markets, event_id, stats, unmapped_tracker
                )
                all_errors.extend(errors)

            # Analyze Bet9ja
            if has_bet9ja and platforms["bet9ja"]["raw_response"]:
                bet9ja_markets = extract_bet9ja_markets(
                    platforms["bet9ja"]["raw_response"]
                )
                errors = analyze_bet9ja_mapping(
                    bet9ja_markets, event_id, stats, unmapped_tracker
                )
                all_errors.extend(errors)

            # Progress indicator
            if i % 10 == 0:
                print(f"  Analyzed {i}/{len(events)} events...")

    # Print summary
    print()
    print("=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print()
    print(f"Events analyzed: {stats.total_events_analyzed}")
    print(f"Events with all 3 platforms: {stats.events_with_all_platforms}")
    print()
    print(f"SportyBet: {stats.sportybet_mapped}/{stats.sportybet_total_markets} mapped "
          f"({stats.sportybet_mapped/max(1, stats.sportybet_total_markets)*100:.1f}%)")
    print(f"Bet9ja: {stats.bet9ja_mapped}/{stats.bet9ja_total_markets} mapped "
          f"({stats.bet9ja_mapped/max(1, stats.bet9ja_total_markets)*100:.1f}%)")
    print()
    print(f"Unique unmapped market types: {len(unmapped_tracker)}")
    print()

    # Task 3: Generate report
    print("TASK 3: Generating audit report...")
    report_path = output_dir / "AUDIT-FINDINGS.md"
    report_content = generate_audit_report(stats, unmapped_tracker, report_path)

    print(f"  Report written to: {report_path}")
    print()

    # Also save raw data as JSON for potential further analysis
    raw_data_path = output_dir / "audit_raw_data.json"
    raw_data = {
        "stats": {
            "total_events_analyzed": stats.total_events_analyzed,
            "events_with_betpawa": stats.events_with_betpawa,
            "events_with_sportybet": stats.events_with_sportybet,
            "events_with_bet9ja": stats.events_with_bet9ja,
            "events_with_all_platforms": stats.events_with_all_platforms,
            "sportybet_total_markets": stats.sportybet_total_markets,
            "sportybet_mapped": stats.sportybet_mapped,
            "sportybet_failed": stats.sportybet_failed,
            "bet9ja_total_markets": stats.bet9ja_total_markets,
            "bet9ja_mapped": stats.bet9ja_mapped,
            "bet9ja_failed": stats.bet9ja_failed,
            "betpawa_total_markets": stats.betpawa_total_markets,
        },
        "unmapped_markets": [
            {
                "platform": m.platform,
                "market_id": m.market_id,
                "market_desc": m.market_desc,
                "error_code": m.error_code,
                "frequency": m.frequency,
                "category": categorize_market(m.market_desc, m.market_id),
            }
            for m in unmapped_tracker.values()
        ],
        "error_codes": {
            "sportybet": dict(stats.sportybet_errors_by_code),
            "bet9ja": dict(stats.bet9ja_errors_by_code),
        },
    }
    raw_data_path.write_text(json.dumps(raw_data, indent=2), encoding="utf-8")
    print(f"  Raw data written to: {raw_data_path}")

    return stats, report_content


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Market Mapping Audit Script")
    parser.add_argument(
        "--min-events",
        type=int,
        default=50,
        help="Minimum number of events to analyze (default: 50)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for reports",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    asyncio.run(run_audit(min_events=args.min_events, output_dir=output_dir))
