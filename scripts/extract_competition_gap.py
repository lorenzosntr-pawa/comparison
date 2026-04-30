"""Extract competition coverage gap between BetPawa and competitors.

Analyzes which tournaments competitors (SportyBet, Bet9ja) offer that
BetPawa doesn't, and measures how many days before kickoff each platform
lists events.

Usage:
    python scripts/extract_competition_gap.py --start 2026-01-01 --end 2026-04-01
    python scripts/extract_competition_gap.py --start 2026-01-01 --end 2026-04-01 --competitor sportybet
    python scripts/extract_competition_gap.py --start 2026-01-01 --end 2026-04-01 -o gap_report.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from src.db.engine import async_session_factory


EXTRACTION_QUERY = """
WITH event_coverage AS (
    SELECT
        ct.source AS competitor,
        ct.id AS competitor_tournament_id,
        ct.name AS competitor_tournament,
        ct.country_raw AS country,
        ce.kickoff,
        ce.created_at AS competitor_created_at,
        ce.betpawa_event_id,
        e.created_at AS betpawa_created_at,
        t.name AS betpawa_tournament
    FROM competitor_events ce
    INNER JOIN competitor_tournaments ct ON ct.id = ce.tournament_id
    LEFT JOIN events e ON e.id = ce.betpawa_event_id
    LEFT JOIN tournaments t ON t.id = e.tournament_id
    WHERE
        ce.kickoff >= :start_date
        AND ce.kickoff < :end_date
        AND ce.deleted_at IS NULL
        AND ct.deleted_at IS NULL
        {competitor_filter}
)

SELECT
    competitor AS "Competitor",
    competitor_tournament AS "Competitor Tournament",
    MODE() WITHIN GROUP (ORDER BY betpawa_tournament) AS "BetPawa Tournament",
    country AS "Country",
    COUNT(*) AS "Total Events (Competitor)",
    COUNT(betpawa_event_id) AS "Total Events (BetPawa)",
    COUNT(*) - COUNT(betpawa_event_id) AS "Missing Events",
    ROUND(
        COUNT(betpawa_event_id)::numeric / COUNT(*)::numeric * 100, 1
    ) AS "Coverage %",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - competitor_created_at)) / 86400.0
        ) FILTER (WHERE competitor_created_at IS NOT NULL),
        1
    ) AS "Avg Days Before KO (Competitor)",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - betpawa_created_at)) / 86400.0
        ) FILTER (WHERE betpawa_event_id IS NOT NULL AND betpawa_created_at IS NOT NULL),
        1
    ) AS "Avg Days Before KO (BetPawa)",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - competitor_created_at)) / 86400.0
            - EXTRACT(EPOCH FROM (kickoff - betpawa_created_at)) / 86400.0
        ) FILTER (WHERE betpawa_event_id IS NOT NULL AND competitor_created_at IS NOT NULL AND betpawa_created_at IS NOT NULL),
        1
    ) AS "Avg Timing Gap (Days)"
FROM event_coverage
GROUP BY competitor, competitor_tournament_id, competitor_tournament, country
ORDER BY "Missing Events" DESC, competitor_tournament
"""

COLUMN_HEADERS = [
    "Competitor",
    "Competitor Tournament",
    "BetPawa Tournament",
    "Country",
    "Total Events (Competitor)",
    "Total Events (BetPawa)",
    "Missing Events",
    "Coverage %",
    "Avg Days Before KO (Competitor)",
    "Avg Days Before KO (BetPawa)",
    "Avg Timing Gap (Days)",
]


async def extract_coverage_gap(
    start_date: str,
    end_date: str,
    competitor: str | None = None,
) -> list[dict[str, Any]]:
    """Extract competition coverage gap data for the given date range.

    Args:
        start_date: Start date (inclusive) in YYYY-MM-DD format.
        end_date: End date (exclusive) in YYYY-MM-DD format.
        competitor: Optional competitor filter ('sportybet' or 'bet9ja').

    Returns:
        List of row dictionaries with coverage gap data per tournament.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    params: dict[str, Any] = {
        "start_date": start_dt,
        "end_date": end_dt,
    }

    if competitor:
        competitor_filter = "AND ct.source = :competitor"
        params["competitor"] = competitor
    else:
        competitor_filter = ""

    query = EXTRACTION_QUERY.format(competitor_filter=competitor_filter)

    async with async_session_factory() as session:
        result = await session.execute(text(query), params)
        rows = result.fetchall()
        return [dict(zip(COLUMN_HEADERS, row)) for row in rows]


def export_to_csv(data: list[dict[str, Any]], output_path: str) -> None:
    """Export extracted data to CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMN_HEADERS)
        writer.writeheader()
        writer.writerows(data)
    print(f"Exported {len(data)} rows to {output_path}")


def print_summary(
    data: list[dict[str, Any]], competitor: str | None
) -> None:
    """Print summary of coverage gap analysis."""
    if not data:
        comp_label = competitor or "all competitors"
        print(f"No data found for {comp_label} in the specified date range.")
        return

    total_tournaments = len(data)
    never_covered = sum(1 for row in data if row["Total Events (BetPawa)"] == 0)
    partial_coverage = sum(
        1 for row in data
        if 0 < row["Total Events (BetPawa)"] < row["Total Events (Competitor)"]
    )
    full_coverage = sum(
        1 for row in data
        if row["Total Events (BetPawa)"] == row["Total Events (Competitor)"]
    )
    total_missing = sum(row["Missing Events"] for row in data)
    timing_gaps = sum(
        1 for row in data
        if row["Avg Timing Gap (Days)"] is not None and row["Avg Timing Gap (Days)"] > 0
    )

    print(f"\nCompetition Coverage Gap Analysis")
    print("=" * 60)
    print(f"Total tournaments analyzed:    {total_tournaments:>6}")
    print(f"Never covered (0%):            {never_covered:>6}")
    print(f"Partial coverage:              {partial_coverage:>6}")
    print(f"Full coverage (100%):          {full_coverage:>6}")
    print(f"Total missing events:          {total_missing:>6}")
    print(f"Tournaments with timing gap:   {timing_gaps:>6}")

    # Show top 10 gaps
    print(f"\nTop gaps (by missing events):")
    print("-" * 80)
    print(
        f"  {'Competitor':<12} {'Tournament':<35} {'Country':<12} "
        f"{'Missing':>7} {'Cov%':>5}"
    )
    print("-" * 80)
    for row in data[:10]:
        tournament = row["Competitor Tournament"][:33]
        country = (row["Country"] or "")[:10]
        coverage = row["Coverage %"]
        print(
            f"  {row['Competitor']:<12} {tournament:<35} {country:<12} "
            f"{row['Missing Events']:>7} {coverage:>5}%"
        )


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract competition coverage gap between BetPawa and competitors"
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (inclusive) in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date (exclusive) in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--competitor",
        choices=["sportybet", "bet9ja"],
        default=None,
        help="Filter by competitor (default: both)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output CSV file path (optional)",
    )

    args = parser.parse_args()

    try:
        datetime.strptime(args.start, "%Y-%m-%d")
        datetime.strptime(args.end, "%Y-%m-%d")
    except ValueError as e:
        print(f"Invalid date format: {e}")
        sys.exit(1)

    comp_label = args.competitor or "all competitors"
    print(f"Extracting coverage gap for {comp_label}")
    print(f"Date range: {args.start} to {args.end}")

    data = await extract_coverage_gap(args.start, args.end, args.competitor)

    print_summary(data, args.competitor)

    if args.output:
        export_to_csv(data, args.output)


if __name__ == "__main__":
    asyncio.run(main())
