"""Verification script for Phase 102: Scraping Verification.

Runs a real scrape cycle after Phase 101 raw_response removal to verify:
1. Scraping completes successfully (status=COMPLETED)
2. Events are scraped (count > 0)
3. No critical errors logged
4. Database schema has raw_response columns removed
5. Data integrity: snapshots and market_odds have valid data

Usage:
    python scripts/verify_scraping.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path for src imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.caching.odds_cache import OddsCache
from src.caching.warmup import warm_cache_from_db
from src.db.engine import async_session_factory
from src.db.models.odds import OddsSnapshot, MarketOdds
from src.db.models.competitor import CompetitorOddsSnapshot, CompetitorMarketOdds
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.event_coordinator import EventCoordinator
from src.storage import AsyncWriteQueue


# ---------------------------------------------------------------------------
# Test 1: Run scrape cycle
# ---------------------------------------------------------------------------

async def run_scrape_and_verify() -> tuple[bool, dict[str, Any]]:
    """Run a full scrape cycle and verify completion.

    Returns:
        Tuple of (success: bool, results: dict with details).
    """
    results: dict[str, Any] = {
        "scrape_run_id": None,
        "status": None,
        "events_scraped": 0,
        "events_failed": 0,
        "errors": [],
    }

    # Create OddsCache and warm from DB
    odds_cache = OddsCache()
    async with async_session_factory() as warmup_db:
        warmup_stats = await warm_cache_from_db(odds_cache, warmup_db)
    print(f"  Cache warmed: {warmup_stats.get('events', 0)} events, {warmup_stats.get('betpawa_snapshots', 0)} betpawa snapshots")

    # Create and start write queue
    write_queue = AsyncWriteQueue(session_factory=async_session_factory, maxsize=50)
    await write_queue.start()

    try:
        async with async_session_factory() as db:
            # Get settings
            result = await db.execute(select(Settings).where(Settings.id == 1))
            settings = result.scalar_one_or_none()

            # Create ScrapeRun
            scrape_run = ScrapeRun(
                status=ScrapeStatus.RUNNING,
                trigger="verification",
            )
            db.add(scrape_run)
            await db.commit()
            await db.refresh(scrape_run)
            results["scrape_run_id"] = scrape_run.id
            print(f"  Created ScrapeRun #{scrape_run.id}")

            # Create HTTP clients
            async with httpx.AsyncClient(
                base_url="https://www.sportybet.com",
                headers={
                    "accept": "*/*",
                    "accept-language": "en",
                    "clientid": "web",
                    "operid": "2",
                    "platform": "web",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=30.0,
                limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
            ) as sportybet_http:
                async with httpx.AsyncClient(
                    base_url="https://www.betpawa.ng",
                    headers={
                        "accept": "*/*",
                        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                        "devicetype": "web",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "x-pawa-brand": "betpawa-nigeria",
                    },
                    timeout=30.0,
                    limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
                ) as betpawa_http:
                    async with httpx.AsyncClient(
                        base_url="https://sports.bet9ja.com",
                        headers={
                            "accept": "application/json, text/plain, */*",
                            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        },
                        timeout=30.0,
                        limits=httpx.Limits(max_connections=200, max_keepalive_connections=100),
                    ) as bet9ja_http:

                        sportybet = SportyBetClient(sportybet_http)
                        betpawa = BetPawaClient(betpawa_http)
                        bet9ja = Bet9jaClient(bet9ja_http)

                        if settings:
                            coordinator = EventCoordinator.from_settings(
                                betpawa_client=betpawa,
                                sportybet_client=sportybet,
                                bet9ja_client=bet9ja,
                                settings=settings,
                                odds_cache=odds_cache,
                                write_queue=write_queue,
                            )
                        else:
                            coordinator = EventCoordinator(
                                betpawa_client=betpawa,
                                sportybet_client=sportybet,
                                bet9ja_client=bet9ja,
                                odds_cache=odds_cache,
                                write_queue=write_queue,
                            )

                        # Run the scrape cycle
                        async for event in coordinator.run_full_cycle(
                            db=db, scrape_run_id=scrape_run.id
                        ):
                            if event.get("event_type") == "CYCLE_COMPLETE":
                                results["events_scraped"] = event.get("events_scraped", 0)
                                results["events_failed"] = event.get("events_failed", 0)
                            elif event.get("event_type") == "ERROR":
                                results["errors"].append(event.get("message", "Unknown error"))

            # Update status to COMPLETED (use naive UTC datetime to match DB schema)
            scrape_run.status = ScrapeStatus.COMPLETED
            scrape_run.completed_at = datetime.utcnow()
            await db.commit()
            results["status"] = "COMPLETED"

    finally:
        # Stop write queue (drains remaining items)
        await write_queue.stop()

    # Determine success
    success = (
        results["status"] == "COMPLETED"
        and results["events_scraped"] > 0
        and len(results["errors"]) == 0
    )

    return success, results


# ---------------------------------------------------------------------------
# Test 2: Validate database integrity
# ---------------------------------------------------------------------------

async def verify_raw_response_removed() -> tuple[bool, dict[str, Any]]:
    """Verify raw_response columns are removed from database schema.

    Returns:
        Tuple of (success: bool, results: dict with details).
    """
    results: dict[str, Any] = {
        "odds_snapshots_has_raw_response": None,
        "competitor_odds_snapshots_has_raw_response": None,
    }

    async with async_session_factory() as db:
        # Check odds_snapshots table
        query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'odds_snapshots'
            AND column_name = 'raw_response'
        """)
        result = await db.execute(query)
        rows = result.fetchall()
        results["odds_snapshots_has_raw_response"] = len(rows) > 0

        # Check competitor_odds_snapshots table
        query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'competitor_odds_snapshots'
            AND column_name = 'raw_response'
        """)
        result = await db.execute(query)
        rows = result.fetchall()
        results["competitor_odds_snapshots_has_raw_response"] = len(rows) > 0

    success = (
        not results["odds_snapshots_has_raw_response"]
        and not results["competitor_odds_snapshots_has_raw_response"]
    )

    return success, results


async def verify_data_integrity() -> tuple[bool, dict[str, Any]]:
    """Verify recent data exists and has valid outcomes.

    Returns:
        Tuple of (success: bool, results: dict with details).
    """
    results: dict[str, Any] = {
        "recent_odds_snapshots": 0,
        "recent_competitor_snapshots": 0,
        "market_odds_with_outcomes": 0,
        "competitor_market_odds_with_outcomes": 0,
        "sample_snapshot": None,
        "sample_market_odds": None,
    }

    async with async_session_factory() as db:
        # Count recent odds_snapshots (last hour)
        query = text("""
            SELECT COUNT(*)
            FROM odds_snapshots
            WHERE captured_at > NOW() - INTERVAL '1 hour'
        """)
        result = await db.execute(query)
        results["recent_odds_snapshots"] = result.scalar() or 0

        # Count recent competitor_odds_snapshots (last hour)
        query = text("""
            SELECT COUNT(*)
            FROM competitor_odds_snapshots
            WHERE captured_at > NOW() - INTERVAL '1 hour'
        """)
        result = await db.execute(query)
        results["recent_competitor_snapshots"] = result.scalar() or 0

        # Count market_odds with non-empty outcomes
        query = text("""
            SELECT COUNT(*)
            FROM market_odds mo
            JOIN odds_snapshots os ON mo.snapshot_id = os.id
            WHERE os.captured_at > NOW() - INTERVAL '1 hour'
            AND mo.outcomes IS NOT NULL
            AND mo.outcomes::text != '[]'
        """)
        result = await db.execute(query)
        results["market_odds_with_outcomes"] = result.scalar() or 0

        # Count competitor_market_odds with non-empty outcomes
        query = text("""
            SELECT COUNT(*)
            FROM competitor_market_odds cmo
            JOIN competitor_odds_snapshots cos ON cmo.snapshot_id = cos.id
            WHERE cos.captured_at > NOW() - INTERVAL '1 hour'
            AND cmo.outcomes IS NOT NULL
            AND cmo.outcomes::text != '[]'
        """)
        result = await db.execute(query)
        results["competitor_market_odds_with_outcomes"] = result.scalar() or 0

        # Get a sample snapshot with market odds
        query = text("""
            SELECT os.id, os.captured_at, mo.betpawa_market_id, mo.outcomes
            FROM odds_snapshots os
            JOIN market_odds mo ON mo.snapshot_id = os.id
            WHERE os.captured_at > NOW() - INTERVAL '1 hour'
            AND mo.outcomes IS NOT NULL
            AND mo.outcomes::text != '[]'
            LIMIT 1
        """)
        result = await db.execute(query)
        row = result.fetchone()
        if row:
            results["sample_snapshot"] = {
                "id": row[0],
                "captured_at": str(row[1]),
            }
            results["sample_market_odds"] = {
                "betpawa_market_id": row[2],
                "outcomes_count": len(row[3]) if row[3] else 0,
            }

    success = (
        results["recent_odds_snapshots"] > 0
        and results["market_odds_with_outcomes"] > 0
    )

    return success, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> int:
    """Run all verification tests."""
    print("=" * 60)
    print("  Phase 102: Scraping Verification")
    print("  Verifying Phase 101 raw_response removal")
    print("=" * 60)
    print()

    all_passed = True

    # Test 1: Run scrape and verify completion
    print("[1/3] Running scrape cycle...")
    try:
        scrape_passed, scrape_results = await run_scrape_and_verify()
        print(f"  Scrape Run ID: {scrape_results['scrape_run_id']}")
        print(f"  Status: {scrape_results['status']}")
        print(f"  Events scraped: {scrape_results['events_scraped']}")
        print(f"  Events failed: {scrape_results['events_failed']}")
        if scrape_results["errors"]:
            print(f"  Errors: {scrape_results['errors']}")

        if scrape_passed:
            print("  [PASS] PASS: Scrape completed successfully")
        else:
            print("  [FAIL] FAIL: Scrape did not complete successfully")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] FAIL: Scrape failed with error: {e}")
        all_passed = False
        scrape_passed = False

    print()

    # Test 2: Verify raw_response columns removed
    print("[2/3] Verifying raw_response columns removed...")
    try:
        schema_passed, schema_results = await verify_raw_response_removed()
        print(f"  odds_snapshots has raw_response: {schema_results['odds_snapshots_has_raw_response']}")
        print(f"  competitor_odds_snapshots has raw_response: {schema_results['competitor_odds_snapshots_has_raw_response']}")

        if schema_passed:
            print("  [PASS] PASS: raw_response columns confirmed removed")
        else:
            print("  [FAIL] FAIL: raw_response columns still exist")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] FAIL: Schema check failed with error: {e}")
        all_passed = False

    print()

    # Test 3: Verify data integrity
    print("[3/3] Verifying data integrity...")
    try:
        data_passed, data_results = await verify_data_integrity()
        print(f"  Recent odds_snapshots (last hour): {data_results['recent_odds_snapshots']}")
        print(f"  Recent competitor_snapshots (last hour): {data_results['recent_competitor_snapshots']}")
        print(f"  market_odds with outcomes: {data_results['market_odds_with_outcomes']}")
        print(f"  competitor_market_odds with outcomes: {data_results['competitor_market_odds_with_outcomes']}")

        if data_results["sample_snapshot"]:
            print(f"  Sample snapshot ID: {data_results['sample_snapshot']['id']}")
            print(f"  Sample market_odds betpawa_market_id: {data_results['sample_market_odds']['betpawa_market_id']}")
            print(f"  Sample outcomes count: {data_results['sample_market_odds']['outcomes_count']}")

        if data_passed:
            print("  [PASS] PASS: Data integrity verified")
        else:
            print("  [FAIL] FAIL: Data integrity issues found")
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] FAIL: Data integrity check failed with error: {e}")
        all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("  [PASS] ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("  [FAIL] SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
