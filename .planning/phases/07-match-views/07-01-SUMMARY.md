---
phase: 07-match-views
plan: 01
subsystem: api
tags: [fastapi, pydantic, odds, margins]

requires:
  - phase: 06.1-cross-platform-scraping
    provides: cross-platform odds data via SportRadar ID matching
provides:
  - inline odds in events list (1X2, O/U 2.5, BTTS)
  - full market data in event detail
  - margin calculations per market
affects: [match-views-frontend, real-time-updates]

tech-stack:
  added: []
  patterns:
    - subquery for latest snapshot per (event_id, bookmaker_id)
    - margin calculation formula

key-files:
  created: []
  modified:
    - src/api/routes/events.py
    - src/matching/schemas.py

key-decisions:
  - "Used subquery approach for efficient latest-snapshot loading"
  - "Extended BookmakerOdds rather than creating new list schema"
  - "EventDetailResponse extends MatchedEvent for backward compatibility"

patterns-established:
  - "Margin calculation: (sum(1/odds) - 1) * 100"
  - "Inline odds for list views: fixed 3 key markets"
  - "Full market data for detail views: all markets with outcomes"

issues-created: []

duration: 6min
completed: 2026-01-21
---

# Phase 7 Plan 1: Events API Odds Enhancement Summary

**Extended events API with inline odds for list view and full market data with margin calculations for detail view**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-21T11:33:32Z
- **Completed:** 2026-01-21T11:39:13Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Events list returns inline odds for key markets (1X2, O/U 2.5, BTTS) per bookmaker
- Event detail returns complete market data with margin calculations
- Efficient subquery approach prevents N+1 queries

## Task Commits

1. **Task 1: Add inline odds to events list endpoint** - `1b44d17` (feat)
2. **Task 2: Create event detail endpoint with full market odds** - `b7ca298` (feat)

## Files Created/Modified

- `src/matching/schemas.py` - Added OutcomeOdds, InlineOdds, OutcomeDetail, MarketOddsDetail, BookmakerMarketData, EventDetailResponse schemas
- `src/api/routes/events.py` - Added inline odds loading, full market data building, margin calculation

## Decisions Made

- Used subquery approach for latest-snapshot loading (avoids N+1 queries)
- Extended BookmakerOdds with inline_odds field rather than creating separate list schema
- EventDetailResponse extends MatchedEvent for full backward compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- API now returns all data needed for frontend match views
- Ready for Plan 07-02: Match list view component

---
*Phase: 07-match-views*
*Completed: 2026-01-21*

### Task 1: Add inline odds to events list endpoint
**Commit:** 1b44d17

Extended the events list endpoint to include latest odds for key markets (1X2, O/U 2.5, BTTS) per bookmaker.

**Changes:**
- Added `OutcomeOdds` schema (name, odds)
- Added `InlineOdds` schema (market_id, market_name, outcomes)
- Extended `BookmakerOdds` with `inline_odds: list[InlineOdds]` field
- Added `_build_inline_odds()` helper to extract key market odds from snapshots
- Added `_load_latest_snapshots_for_events()` for efficient batch loading
- Updated both `list_events()` and `get_event()` to include inline odds

**Files Modified:**
- `src/matching/schemas.py`
- `src/api/routes/events.py`

### Task 2: Create event detail endpoint with full market odds
**Commit:** b7ca298

Enhanced GET /events/{id} to return complete market odds for all bookmakers with margin calculations.

**Changes:**
- Added `OutcomeDetail` schema (name, odds, is_active)
- Added `MarketOddsDetail` schema (betpawa_market_id, betpawa_market_name, line, outcomes, margin)
- Added `BookmakerMarketData` schema (bookmaker_slug, bookmaker_name, snapshot_time, markets)
- Added `EventDetailResponse` extending `MatchedEvent` with `markets_by_bookmaker`
- Added `_calculate_margin()` helper: (sum(1/odds) - 1) * 100
- Added `_build_market_detail()` and `_build_bookmaker_market_data()` helpers
- Updated `get_event()` to return `EventDetailResponse` with full market data

**Files Modified:**
- `src/matching/schemas.py`
- `src/api/routes/events.py`

## API Response Structure

### List Events (GET /events)
```json
{
  "events": [{
    "id": 123,
    "name": "Team A vs Team B",
    "bookmakers": [{
      "bookmaker_slug": "betpawa",
      "has_odds": true,
      "inline_odds": [
        {"market_id": "1", "market_name": "1X2", "outcomes": [{"name": "1", "odds": 1.85}]}
      ]
    }]
  }]
}
```

### Event Detail (GET /events/{id})
```json
{
  "id": 123,
  "name": "Team A vs Team B",
  "bookmakers": [...],
  "markets_by_bookmaker": [{
    "bookmaker_slug": "betpawa",
    "snapshot_time": "2026-01-21T12:00:00Z",
    "markets": [{
      "betpawa_market_id": "1",
      "betpawa_market_name": "1X2",
      "outcomes": [{"name": "1", "odds": 1.85, "is_active": true}],
      "margin": 5.2
    }]
  }]
}
```

## Technical Notes

- **Efficient Loading:** Uses subquery to fetch only latest snapshot per (event_id, bookmaker_id) pair, avoiding N+1 queries
- **Market IDs:** Key markets are "1" (1X2), "18" (O/U 2.5), "29" (BTTS) per Betpawa taxonomy
- **Margin Calculation:** `(sum(1/odds for each outcome) - 1) * 100`, rounded to 2 decimal places
- **Backward Compatibility:** `EventDetailResponse` extends `MatchedEvent`, preserving all existing fields

## Deviations

None. Implementation followed the plan exactly.

## Verification Status

- [x] Events list includes inline_odds per bookmaker
- [x] Event detail includes markets_by_bookmaker with full odds
- [x] Margin calculation implemented correctly
- [x] Missing odds handled gracefully (empty arrays)
- [x] Efficient batch loading prevents N+1 queries
