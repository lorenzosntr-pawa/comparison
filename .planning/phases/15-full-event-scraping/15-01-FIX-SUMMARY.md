# Fix Summary: 15-01-FIX Full Market Depth

**Plan:** 15-01-FIX
**Type:** Fix
**Status:** Complete
**Duration:** ~10 min

## Issue Addressed

**UAT-001:** Competitor event scraping only captures main markets from tournament listings

The original implementation scraped odds from tournament listing pages which only included main markets (1X2, Over/Under, BTTS). Individual event pages contain many more markets that were not being captured.

## Changes Made

### Task 1: Add full market fetching to CompetitorEventScrapingService

**File:** `src/scraping/competitor_events.py`

Added new methods:
- `_fetch_full_sportybet_odds()` - Fetches single event with ALL markets via fetch_event()
- `_fetch_full_bet9ja_odds()` - Fetches single event with ALL odds via fetch_event()
- `_update_snapshot_with_full_odds()` - Replaces initial markets with full set, updates raw_response
- `scrape_full_odds_for_events()` - Orchestrates full odds fetching with concurrency control

Modified existing methods:
- `scrape_sportybet_events()` - Now accepts `fetch_full_odds: bool = True` parameter, collects snapshot IDs, calls full odds fetcher
- `scrape_bet9ja_events()` - Same modifications as SportyBet
- `scrape_all()` - Updated to include `events_with_full_odds` in results dict

**Concurrency:**
- SportyBet: 30 concurrent requests
- Bet9ja: 10 concurrent requests
- Batch size: 50 events at a time
- Progress logging every 100 events

**Commit:** `252b566` fix(15-01-FIX): add full market depth fetching for competitor events

### Task 2: Update API endpoint to report full odds stats

**Files:**
- `src/api/schemas/scheduler.py`
- `src/api/routes/scheduler.py`

Added `events_with_full_odds: int = 0` field to `CompetitorScrapeResult` schema.

Updated `scrape_competitor_events` endpoint to include the new field in response.

**Commit:** `2d68738` fix(15-01-FIX): update API to report full odds statistics

## Verification

After running `POST /api/scheduler/scrape-competitor-events`:
- Response includes `events_with_full_odds` field for both platforms
- Market count reflects full market depth (50-100+ per event vs 3-8 before)
- `competitor_odds_snapshots.raw_response` contains complete event data
- `competitor_market_odds` contains all mapped markets from individual event fetch

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `252b566` | Add full market depth fetching |
| 2 | `2d68738` | Update API to report full odds stats |
| Meta | (pending) | Documentation commit |

## Files Modified

- `src/scraping/competitor_events.py` (+344, -28)
- `src/api/schemas/scheduler.py` (+1)
- `src/api/routes/scheduler.py` (+2)
