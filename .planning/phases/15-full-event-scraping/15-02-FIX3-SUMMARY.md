# 15-02-FIX3 Summary: Session Concurrency Fix

**Plan:** 15-02-FIX3.md
**Status:** Complete
**Duration:** ~30 min

## Objective

Fix SQLAlchemy async session concurrency errors that caused mass tournament failures when running competitor scraping through the orchestrator.

## Root Cause

The competitor scraping code interleaved API calls and DB writes in parallel, violating SQLAlchemy's AsyncSession constraint: sessions cannot be shared across concurrent asyncio tasks.

**BetPawa pattern (worked):** Fetch-then-store - all API calls first (parallel), then all DB writes (sequential)

**Competitor pattern (broken):** Mixed API+DB in parallel within `process_tournament()` function

## Changes Made

### Task 1-3: Refactor CompetitorEventScrapingService (b59fb2d)

Restructured `src/scraping/competitor_events.py` to use fetch-then-store pattern:

**New methods created:**
- `_fetch_sportybet_events_api_only()` - Phase 1: parallel API calls, no DB
- `_store_sportybet_events_sequential()` - Phase 2: sequential DB writes
- `_fetch_bet9ja_events_api_only()` - Same pattern for Bet9ja
- `_store_bet9ja_events_sequential()` - Same pattern for Bet9ja
- `_fetch_full_odds_api_only()` - Phase 1 for full odds fetching
- `_update_snapshots_with_odds_sequential()` - Phase 2 for full odds storage

**Updated public methods:**
- `scrape_sportybet_events()` - Orchestrates 3 phases
- `scrape_bet9ja_events()` - Orchestrates 3 phases
- `scrape_full_odds_for_events()` - Uses fetch-then-store

### Task 4: Session Cleanup & Sequential Scraping (a4448f8)

**Orchestrator changes (`src/scraping/orchestrator.py`):**
- Changed from `asyncio.gather(sportybet, bet9ja)` to sequential execution
- SportyBet completes fully before Bet9ja starts
- Ensures AsyncSession is never shared across concurrent tasks

**Transaction boundary fixes (`src/scraping/competitor_events.py`):**
- Added `db.commit()` after tournament queries (before API phase)
- Added `db.commit()` after event storage (before full odds phase)
- Added `db.commit()` after full odds storage (before returning)

### Bonus Fix: API Status Comparison (3103b13)

Fixed `src/api/routes/scrape.py` line 684-687:
- `scrape_run.status` is a string, not enum
- Changed comparison to use `.value` on enum side

## Verification

Successful scrape via UI "Run Scrape" button:

```
[info] scrape_complete betpawa=1076 competitors=2605 scrape_run_id=21 total_events=3681
```

- No "Session is already flushing" errors
- No "cannot perform operation: another operation is in progress" errors
- All tournaments completed successfully
- GET /api/events returns 200
- competitor_events populated from both platforms
- 65,301 markets from Bet9ja full odds

## Commits

| Hash | Type | Description |
|------|------|-------------|
| b59fb2d | refactor | fetch-then-store pattern for competitor scraping |
| a4448f8 | fix | session cleanup and sequential competitor scraping |
| 3103b13 | fix | status comparison in scrape progress endpoint |

## Lessons Learned

1. SQLAlchemy AsyncSession cannot be shared across concurrent asyncio tasks
2. The fetch-then-store pattern (like BetPawa uses) is the correct architecture
3. Transaction boundaries must be explicit between phases
4. Sequential competitor scraping is safer than parallel when sharing a session
