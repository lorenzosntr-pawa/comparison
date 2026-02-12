---
phase: 99-availability-tracking-fix
plan: 01
subsystem: database
tags: [availability, write-queue, persistence, sqlalchemy]

# Dependency graph
requires:
  - phase: 87-investigation-schema-design
    provides: unavailable_at column in market_odds table
  - phase: 88-backend-availability-tracking
    provides: availability detection logic
provides:
  - unavailable_at field persistence to database
  - UnavailableMarketUpdate dataclass for update operations
  - WriteBatch unavailable market support
affects: [api, frontend-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "UnavailableMarketUpdate pattern for batch UPDATE operations"
    - "Detection-to-persistence pipeline for availability tracking"

key-files:
  created: []
  modified:
    - src/storage/write_queue.py
    - src/storage/write_handler.py
    - src/scraping/event_coordinator.py

key-decisions:
  - "Use UPDATE queries for existing rows rather than INSERT replacement"
  - "Wire both async and sync paths for complete coverage"

patterns-established:
  - "UnavailableMarketUpdate dataclass for tracking markets that became unavailable"
  - "Separate INSERT path (new markets) from UPDATE path (unavailable existing markets)"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-12
---

# Phase 99 Plan 01: Availability Tracking Fix Summary

**Wire availability detection through to database persistence - markets that disappear from scrapes now have unavailable_at timestamp saved to DB**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-12
- **Completed:** 2026-02-12
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `unavailable_at` field to `MarketWriteData` dataclass for new market inserts
- Created `UnavailableMarketUpdate` dataclass for UPDATE operations on existing markets
- Extended `WriteBatch` with `unavailable_betpawa` and `unavailable_competitor` fields
- Updated write handler to execute UPDATE queries for unavailable markets
- Wired detection results into WriteBatch in async path
- Added direct UPDATE queries for sync fallback path
- All 92 tests pass with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Add unavailable_at to MarketWriteData and write handler** - `77a7dc0` (feat)
2. **Task 2: Add availability update path to WriteBatch** - `a950abe` (feat)
3. **Task 3: Wire detection results into write batch** - `f80138b` (feat)

## Files Created/Modified

- `src/storage/write_queue.py` - Added datetime import, unavailable_at field to MarketWriteData, UnavailableMarketUpdate dataclass, extended WriteBatch with unavailable fields
- `src/storage/write_handler.py` - Pass unavailable_at to ORM models, add UPDATE logic for unavailable markets, include counts in stats
- `src/scraping/event_coordinator.py` - Return UnavailableMarketUpdate lists from detection functions, wire to WriteBatch, add sync path UPDATEs

## Decisions Made

- **UPDATE vs INSERT:** Markets that become unavailable are existing DB rows that need unavailable_at set via UPDATE, not new rows to INSERT. This preserves the historical record while marking the market as no longer offered.
- **Dual-path coverage:** Both async (WriteBatch) and sync (direct db.execute) paths handle unavailability to ensure complete coverage regardless of execution mode.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed plan without issues.

## Next Phase Readiness

Phase 99 complete. v2.7 Availability Tracking Bugfix milestone ready to ship.

---
*Phase: 99-availability-tracking-fix*
*Completed: 2026-02-12*
