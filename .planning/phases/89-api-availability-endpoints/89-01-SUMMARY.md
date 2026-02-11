---
phase: 89-api-availability-endpoints
plan: 01
subsystem: api
tags: [pydantic, fastapi, availability, market-odds]

# Dependency graph
requires:
  - phase: 88-backend-availability-tracking
    provides: CachedMarket.unavailable_at field, MarketOdds.unavailable_at column
provides:
  - API responses include available/unavailable_since fields on market objects
  - Frontend can distinguish "never offered" from "became unavailable"
affects: [90-frontend-unavailable-styling]

# Tech tracking
tech-stack:
  added: []
  patterns: [getattr-safe-access-for-optional-columns]

key-files:
  created: []
  modified:
    - src/matching/schemas.py
    - src/api/routes/events.py

key-decisions:
  - "Default values (True, None) maintain backward compatibility"
  - "getattr() pattern for safe access across cache and DB paths"

patterns-established:
  - "Availability extraction pattern: unavailable_at = getattr(market, 'unavailable_at', None); available = unavailable_at is None"

issues-created: []

# Metrics
duration: 2min
completed: 2026-02-11
---

# Phase 89 Plan 01: API Availability Endpoints Summary

**Added available (bool) and unavailable_since (datetime) fields to InlineOdds and MarketOddsDetail schemas with backward-compatible defaults**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-11T15:36:35Z
- **Completed:** 2026-02-11T15:39:05Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `available: bool = True` and `unavailable_since: datetime | None = None` to InlineOdds schema
- Added same fields to MarketOddsDetail schema for detail view
- Updated all 4 API response builders to extract and pass availability data
- All 92 tests pass, no breaking changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Pydantic schemas with availability fields** - `cdc8984` (feat)
2. **Task 2: Update API response builders to pass availability data** - `93dc02b` (feat)

## Files Created/Modified

- `src/matching/schemas.py` - Added available/unavailable_since fields to InlineOdds and MarketOddsDetail
- `src/api/routes/events.py` - Updated _build_inline_odds, _build_competitor_inline_odds, _build_market_detail, _build_competitor_market_detail

## Decisions Made

- Used default values (True, None) to maintain backward compatibility with existing consumers
- Used getattr() pattern for safe access across cache (CachedMarket) and DB (ORM model) paths

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- API now returns `available` and `unavailable_since` on all market objects
- Phase 90 can style unavailable markets based on these fields
- Frontend can distinguish "never offered" (null) from "became unavailable" (with timestamp)

---
*Phase: 89-api-availability-endpoints*
*Completed: 2026-02-11*
