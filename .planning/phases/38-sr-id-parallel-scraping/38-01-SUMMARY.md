---
phase: 38-sr-id-parallel-scraping
plan: 01
subsystem: scraping
tags: [asyncio, semaphore, parallel, event-coordinator]

# Dependency graph
requires:
  - phase: 37-event-coordination-layer
    provides: EventCoordinator with discovery and priority queue
provides:
  - EventTarget.platform_ids for platform-specific API calls
  - scrape_batch() async generator for SSE progress streaming
  - _scrape_event_all_platforms() for parallel multi-platform fetching
  - PLATFORM_SEMAPHORES (50/50/15) and BET9JA_DELAY_MS (25ms)
affects: [39-batch-db-storage, 40-concurrency-tuning]

# Tech tracking
tech-stack:
  added: []
  patterns: [parallel-platform-scraping, semaphore-per-platform, async-generator-progress]

key-files:
  created: []
  modified: [src/scraping/schemas/coordinator.py, src/scraping/event_coordinator.py]

key-decisions:
  - "platform_ids dict stores platform-specific IDs separate from sr_id"
  - "BetPawa uses event_data['id'], SportyBet uses full sr:match: format, Bet9ja uses event_data['ID']"
  - "Partial success (some platforms) = COMPLETED, total failure = FAILED"
  - "Semaphores reused across entire batch for consistent rate limiting"

patterns-established:
  - "Parallel platform scraping: single event → all platforms in parallel via semaphores"
  - "Progress streaming: yield dict events for SSE consumption"

issues-created: []

# Metrics
duration: 3min
completed: 2026-01-29
---

# Phase 38 Plan 01: SR ID Parallel Scraping Summary

**EventTarget extended with platform_ids, scrape_batch() async generator for simultaneous multi-bookmaker scraping with semaphore-based rate limiting**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-29T15:45:00Z
- **Completed:** 2026-01-29T15:48:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Extended EventTarget with `platform_ids: dict[str, str]` for platform-specific event IDs
- Updated all three parse methods to extract and return platform IDs (BetPawa ID, sr:match: format, Bet9ja ID)
- Implemented `_scrape_event_all_platforms()` with per-platform semaphore control
- Implemented `scrape_batch()` async generator yielding EVENT_SCRAPING and EVENT_SCRAPED progress events
- Added PLATFORM_SEMAPHORES (50/50/15) and BET9JA_DELAY_MS (25ms) constants per Phase 36 design

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend EventTarget with platform IDs** - `9d1f62f` (feat)
2. **Task 2: Implement parallel platform scraping** - `569fb3e` (feat)

## Files Created/Modified

- `src/scraping/schemas/coordinator.py` - Added platform_ids field to EventTarget dataclass
- `src/scraping/event_coordinator.py` - Updated parse methods, discovery merge logic, added scrape_batch and _scrape_event_all_platforms

## Decisions Made

- **Platform ID extraction**: BetPawa uses `event_data["id"]`, SportyBet keeps full `sr:match:` format (as API expects), Bet9ja uses `event_data["ID"]` (not EXTID which is SR ID)
- **Status logic**: Event is COMPLETED if any data retrieved (partial success), FAILED only if complete failure
- **Semaphore reuse**: Create semaphores once per batch, reuse across all events for consistent rate limiting

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- EventCoordinator now has complete scrape flow: discovery → priority queue → batch scraping
- Results populated in EventTarget.results and EventTarget.errors
- Ready for Phase 39: Batch DB Storage to persist scraped data
- Progress events ready for SSE streaming integration

---
*Phase: 38-sr-id-parallel-scraping*
*Completed: 2026-01-29*
