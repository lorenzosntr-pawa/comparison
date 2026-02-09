---
phase: 70-backend-freshness-fixes
plan: 01
subsystem: api
tags: [cache, timestamps, freshness, odds_cache]

# Dependency graph
requires:
  - phase: 69-investigation-freshness-audit
    provides: Root cause analysis of staleness issue
provides:
  - last_confirmed_at field in CachedSnapshot
  - Fresh timestamps in API regardless of whether odds changed
  - Consistent freshness across all snapshot types
affects: [71-frontend-freshness-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_get_snapshot_time() helper for consistent timestamp handling"

key-files:
  created: []
  modified:
    - src/caching/odds_cache.py
    - src/caching/warmup.py
    - src/scraping/event_coordinator.py
    - src/api/routes/events.py

key-decisions:
  - "Add last_confirmed_at field to CachedSnapshot dataclass"
  - "Use helper function for DRY timestamp extraction across 7 locations"
  - "Fall back to captured_at for backward compatibility with old data"

patterns-established:
  - "_get_snapshot_time() helper: prefer last_confirmed_at over captured_at with fallback"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-09
---

# Phase 70 Plan 01: Backend Freshness Fixes Summary

**Added `last_confirmed_at` to CachedSnapshot and plumbed it through cache helpers and API to show accurate freshness timestamps**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-09T10:00:00Z
- **Completed:** 2026-02-09T10:08:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Added `last_confirmed_at: datetime` field to CachedSnapshot frozen dataclass
- Updated all 3 cache helper functions to accept and pass the new field
- Updated all 4 call sites in EventCoordinator (async and sync paths)
- Updated all 7 locations in events.py API to use `last_confirmed_at` for `snapshot_time`
- Created `_get_snapshot_time()` helper for consistent handling with fallback to `captured_at`

## Task Commits

Each task was committed atomically:

1. **Task 1: Add last_confirmed_at to CachedSnapshot** - `74d25c7` (feat)
2. **Task 2: Update cache helpers and callers** - `a8aa641` (feat)
3. **Task 3: Update events.py API** - `3383ddb` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/caching/odds_cache.py` - Added `last_confirmed_at` field to CachedSnapshot dataclass
- `src/caching/warmup.py` - Updated 3 cache helper functions with new parameter
- `src/scraping/event_coordinator.py` - Updated 4 call sites (async + sync fallback paths)
- `src/api/routes/events.py` - Added `_get_snapshot_time()` helper, updated 7 snapshot_time assignments

## Decisions Made

- **Helper function over inline logic:** Created `_get_snapshot_time()` helper to avoid repeating the same fallback logic 7 times and ensure consistent behavior
- **Backward compatibility:** Fall back to `captured_at` when `last_confirmed_at` is None (for old data or cache entries created before this change)
- **Field ordering:** Placed `last_confirmed_at` after `captured_at` in CachedSnapshot for logical field grouping

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Phase 71 (Frontend Freshness Fixes) ready:
- Backend now returns correct `snapshot_time` values based on `last_confirmed_at`
- Timestamps will be fresh (within 2 minutes of current time) after each scrape cycle
- Frontend needs to:
  - Subscribe to `odds_updates` WebSocket topic
  - Invalidate TanStack Query cache on `odds_update` messages
  - Ensure timestamps update in real-time without page refresh

---
*Phase: 70-backend-freshness-fixes*
*Completed: 2026-02-09*
