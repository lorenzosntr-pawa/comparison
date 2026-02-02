"""Verify market mapping fixes for NO_MATCHING_OUTCOMES markets.

Spot-check that the fixed markets now map successfully.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.engine import async_session_factory
from src.db.models import (
    CompetitorEvent,
    CompetitorSource,
)
from src.market_mapping.mappers.bet9ja import map_bet9ja_market_to_betpawa
from src.market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from src.market_mapping.types.sportybet import SportybetMarket
from market_mapping.types.errors import MappingError
from market_mapping.utils import parse_bet9ja_key


TARGET_MARKETS_BET9JA = ["HTFTOU", "TMGHO", "TMGAW", "HTFTCS", "HAOU"]
TARGET_MARKETS_SPORTYBET = ["551", "46"]


async def verify_bet9ja_markets():
    """Verify bet9ja market mapping fixes."""
    print("\n=== BET9JA MARKET VERIFICATION ===\n")

    results = {market: {"success": 0, "failed": 0, "errors": []} for market in TARGET_MARKETS_BET9JA}

    async with async_session_factory() as session:
        query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.source == CompetitorSource.BET9JA)
            .options(selectinload(CompetitorEvent.odds_snapshots))
            .limit(30)
        )
        result = await session.execute(query)
        events = result.scalars().unique().all()

        for event in events:
            for snapshot in event.odds_snapshots:
                if not snapshot.raw_response:
                    continue

                odds_data = snapshot.raw_response.get("O", {})

                # Group by market+param
                market_groups = {}
                for key, value in odds_data.items():
                    if not key.startswith("S_"):
                        continue
                    parsed = parse_bet9ja_key(key)
                    if not parsed or parsed.market not in TARGET_MARKETS_BET9JA:
                        continue
                    group_key = (parsed.market, parsed.param)
                    if group_key not in market_groups:
                        market_groups[group_key] = {}
                    market_groups[group_key][parsed.outcome] = str(value)

                # Test each market group
                for (market_key, param), outcomes in market_groups.items():
                    try:
                        mapped = map_bet9ja_market_to_betpawa(market_key, param, outcomes)
                        results[market_key]["success"] += 1
                    except MappingError as e:
                        results[market_key]["failed"] += 1
                        if len(results[market_key]["errors"]) < 3:
                            results[market_key]["errors"].append({
                                "code": str(e.code),
                                "param": param,
                                "outcomes": list(outcomes.keys())[:5],
                            })

    # Print results
    print("Market Verification Results:\n")
    for market, stats in results.items():
        total = stats["success"] + stats["failed"]
        if total == 0:
            print(f"  {market}: No samples found")
        else:
            rate = stats["success"] / total * 100
            status = "PASS" if rate > 90 else "WARN" if rate > 50 else "FAIL"
            print(f"  {status} {market}: {stats['success']}/{total} ({rate:.1f}%)")
            if stats["errors"]:
                for err in stats["errors"][:2]:
                    print(f"      Error: {err['code']}, param={err['param']}, outcomes={err['outcomes']}")


async def verify_sportybet_markets():
    """Verify sportybet market mapping fixes."""
    print("\n\n=== SPORTYBET MARKET VERIFICATION ===\n")

    results = {market: {"success": 0, "failed": 0, "errors": []} for market in TARGET_MARKETS_SPORTYBET}

    async with async_session_factory() as session:
        query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.source == CompetitorSource.SPORTYBET)
            .options(selectinload(CompetitorEvent.odds_snapshots))
            .limit(30)
        )
        result = await session.execute(query)
        events = result.scalars().unique().all()

        for event in events:
            for snapshot in event.odds_snapshots:
                if not snapshot.raw_response:
                    continue

                if "data" in snapshot.raw_response and isinstance(snapshot.raw_response["data"], dict):
                    raw_markets = snapshot.raw_response["data"].get("markets", [])
                elif "markets" in snapshot.raw_response:
                    raw_markets = snapshot.raw_response.get("markets", [])
                else:
                    continue

                for market_data in raw_markets:
                    market_id = str(market_data.get("id", ""))
                    if market_id not in TARGET_MARKETS_SPORTYBET:
                        continue

                    try:
                        market = SportybetMarket.model_validate(market_data)
                        mapped = map_sportybet_to_betpawa(market)
                        results[market_id]["success"] += 1
                    except MappingError as e:
                        results[market_id]["failed"] += 1
                        if len(results[market_id]["errors"]) < 3:
                            results[market_id]["errors"].append({
                                "code": str(e.code),
                                "desc": market_data.get("desc"),
                                "outcome_descs": [o.get("desc") for o in market_data.get("outcomes", [])[:5]],
                            })
                    except Exception as e:
                        results[market_id]["failed"] += 1
                        if len(results[market_id]["errors"]) < 3:
                            results[market_id]["errors"].append({
                                "code": "EXCEPTION",
                                "msg": str(e)[:100],
                            })

    # Print results
    print("Market Verification Results:\n")
    for market, stats in results.items():
        total = stats["success"] + stats["failed"]
        if total == 0:
            print(f"  {market}: No samples found")
        else:
            rate = stats["success"] / total * 100
            status = "PASS" if rate > 90 else "WARN" if rate > 50 else "FAIL"
            print(f"  [{status}] {market}: {stats['success']}/{total} ({rate:.1f}%)")
            if stats["errors"]:
                for err in stats["errors"][:2]:
                    print(f"      Error: {err}")


async def main():
    await verify_bet9ja_markets()
    await verify_sportybet_markets()
    print("\n\n=== VERIFICATION COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
