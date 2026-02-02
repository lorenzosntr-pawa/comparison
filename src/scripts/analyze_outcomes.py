"""Analyze actual outcome structures for NO_MATCHING_OUTCOMES markets.

Quick script to extract sample outcomes for fixing market mappings.
"""

import asyncio
import json
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
from market_mapping.utils import parse_bet9ja_key


TARGET_MARKETS = {
    "bet9ja": ["HTFTOU", "TMGHO", "TMGAW", "HTFTCS", "HAOU"],
    "sportybet": ["551", "46"],  # Multiscores, HT/FT Correct Score
}


async def analyze_bet9ja_outcomes():
    """Find actual outcome suffixes for bet9ja markets."""
    print("\n=== BET9JA OUTCOME ANALYSIS ===\n")

    async with async_session_factory() as session:
        # Get events with bet9ja data
        query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.source == CompetitorSource.BET9JA)
            .options(selectinload(CompetitorEvent.odds_snapshots))
            .limit(50)
        )
        result = await session.execute(query)
        events = result.scalars().unique().all()

        # Collect outcomes per market
        market_outcomes = {}

        for event in events:
            for snapshot in event.odds_snapshots:
                if not snapshot.raw_response:
                    continue

                odds_data = snapshot.raw_response.get("O", {})
                for key, value in odds_data.items():
                    if not key.startswith("S_"):
                        continue

                    parsed = parse_bet9ja_key(key)
                    if not parsed:
                        continue

                    if parsed.market in TARGET_MARKETS["bet9ja"]:
                        market_key = f"{parsed.market}@{parsed.param}" if parsed.param else parsed.market
                        if market_key not in market_outcomes:
                            market_outcomes[market_key] = {"suffixes": set(), "samples": []}
                        market_outcomes[market_key]["suffixes"].add(parsed.outcome)
                        if len(market_outcomes[market_key]["samples"]) < 5:
                            market_outcomes[market_key]["samples"].append({
                                "key": key,
                                "outcome": parsed.outcome,
                                "odds": value
                            })

        # Print findings
        for market, data in sorted(market_outcomes.items()):
            print(f"\n### {market}")
            print(f"Unique outcome suffixes: {sorted(data['suffixes'])}")
            print("Sample keys:")
            for sample in data["samples"][:5]:
                print(f"  - {sample['key']} = {sample['odds']}")


async def analyze_sportybet_outcomes():
    """Find actual outcome descriptions for sportybet markets."""
    print("\n\n=== SPORTYBET OUTCOME ANALYSIS ===\n")

    async with async_session_factory() as session:
        # Get events with sportybet data
        query = (
            select(CompetitorEvent)
            .where(CompetitorEvent.source == CompetitorSource.SPORTYBET)
            .options(selectinload(CompetitorEvent.odds_snapshots))
            .limit(50)
        )
        result = await session.execute(query)
        events = result.scalars().unique().all()

        # Collect outcomes per market
        market_outcomes = {}

        for event in events:
            for snapshot in event.odds_snapshots:
                if not snapshot.raw_response:
                    continue

                # SportyBet structure
                if "data" in snapshot.raw_response and isinstance(snapshot.raw_response["data"], dict):
                    raw_markets = snapshot.raw_response["data"].get("markets", [])
                elif "markets" in snapshot.raw_response:
                    raw_markets = snapshot.raw_response.get("markets", [])
                else:
                    continue

                for market in raw_markets:
                    market_id = str(market.get("id", ""))
                    if market_id in TARGET_MARKETS["sportybet"]:
                        if market_id not in market_outcomes:
                            market_outcomes[market_id] = {
                                "desc": market.get("desc", ""),
                                "outcomes": set(),
                                "samples": []
                            }

                        outcomes = market.get("outcomes", [])
                        for o in outcomes:
                            desc = o.get("desc", "")
                            market_outcomes[market_id]["outcomes"].add(desc)

                        if len(market_outcomes[market_id]["samples"]) < 3:
                            market_outcomes[market_id]["samples"].append({
                                "specifier": market.get("specifier"),
                                "outcome_list": [
                                    {"desc": o.get("desc"), "odds": o.get("odds")}
                                    for o in outcomes[:10]  # First 10 outcomes
                                ]
                            })

        # Print findings
        for market_id, data in sorted(market_outcomes.items()):
            print(f"\n### Market {market_id}: {data['desc']}")
            print(f"Unique outcome descriptions ({len(data['outcomes'])}):")
            for outcome in sorted(data['outcomes'])[:20]:
                print(f"  - {outcome}")
            if len(data['outcomes']) > 20:
                print(f"  ... and {len(data['outcomes']) - 20} more")
            print("\nSample markets:")
            for sample in data["samples"][:2]:
                print(f"  Specifier: {sample['specifier']}")
                for o in sample['outcome_list'][:8]:
                    print(f"    - {o['desc']}: {o['odds']}")


async def main():
    await analyze_bet9ja_outcomes()
    await analyze_sportybet_outcomes()


if __name__ == "__main__":
    asyncio.run(main())
