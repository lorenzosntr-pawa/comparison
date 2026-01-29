---
phase: 41-on-demand-api
plan: 01
subsystem: api
tags: [fastapi, scraping, on-demand, parallel]

# Dependency graph
requires:
  - phase: 38-sr-id-parallel-scraping
    provides: EventTarget with platform_ids, parallel scraping pattern
  - phase: 39-batch-db-storage
    provides: EventScrapeStatus for tracking
  - phase: 40-concurrency-tuning-metrics
    provides: Configurable concurrency settings
provides:
  - POST /api/scrape/event/{sr_id} endpoint for single-event refresh
  - SingleEventScrapeResponse and SingleEventPlatformResult schemas
affects: [frontend-integration, trader-tools]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Parallel platform scraping with asyncio.gather
    - Platform ID lookup from Event and CompetitorEvent tables

key-files:
  created: []
  modified:
    - src/api/schemas/scheduler.py
    - src/api/schemas/__init__.py
    - src/api/routes/scrape.py

key-decisions:
  - "Use /event/{sr_id} path to avoid route conflicts with existing integer-based endpoints"
  - "SportyBet ID format: sr:match:{sr_id} used directly without requiring CompetitorEvent lookup"

patterns-established:
  - "Single-event on-demand scrape with per-platform timing and error details"

issues-created: []

# Metrics
duration: 5min
completed: 2026-01-29
---

# Phase 41 Plan 01: On-Demand API Summary

**POST /api/scrape/event/{sr_id} endpoint for manual single-event refresh across all bookmakers with per-platform timing and error tracking**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-29T14:30:00Z
- **Completed:** 2026-01-29T14:35:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added SingleEventPlatformResult and SingleEventScrapeResponse Pydantic schemas
- Implemented POST /api/scrape/event/{sr_id} endpoint with parallel platform scraping
- Platform ID lookup from Event (BetPawa) and CompetitorEvent (SportyBet, Bet9ja) tables
- Per-platform success/failure tracking with timing and error details

## Task Commits

Each task was committed atomically:

1. **Task 1: Add single-event scrape response schemas** - `705ffaf` (feat)
2. **Task 2: Add POST /api/scrape/event/{sr_id} endpoint** - `f43c5af` (feat)

## Files Created/Modified

- `src/api/schemas/scheduler.py` - Added SingleEventPlatformResult and SingleEventScrapeResponse schemas
- `src/api/schemas/__init__.py` - Exported new schemas
- `src/api/routes/scrape.py` - Added scrape_single_event endpoint with parallel platform scraping

## Decisions Made

- Used `/event/{sr_id}` path instead of `/{sr_id}` to avoid route conflicts with existing `/{scrape_run_id}` integer-based endpoints
- SportyBet ID formatted as `sr:match:{sr_id}` when not found in CompetitorEvent table

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Ready for Phase 42: Validation & Cleanup

---
*Phase: 41-on-demand-api*
*Completed: 2026-01-29*
