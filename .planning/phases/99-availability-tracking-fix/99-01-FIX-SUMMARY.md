---
phase: 99-availability-tracking-fix
plan: 01-FIX
subsystem: scraping
tags: [availability, reconciliation, cache, sqlalchemy]

# Dependency graph
requires:
  - phase: 99-availability-tracking-fix
    provides: unavailable_at persistence to database
provides:
  - Reconciliation for events dropped from discovery
  - Cache-to-DB consistency for unavailable status
  - DiscoveryResult dataclass for per-platform SR ID tracking
affects: [api, frontend-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DiscoveryResult for per-platform SR ID tracking during discovery"
    - "Post-cycle reconciliation to detect events dropped from platforms"
    - "Dual update pattern: DB first, cache immediately after"

key-files:
  created: []
  modified:
    - src/scraping/schemas/coordinator.py
    - src/scraping/event_coordinator.py
    - src/caching/odds_cache.py

key-decisions:
  - "Query DB for event_id->sr_id mapping during reconciliation rather than storing in cache"
  - "Update cache immediately after DB UPDATE for instant API effect"

patterns-established:
  - "DiscoveryResult dataclass for tracking discovered SR IDs per platform"
  - "mark_snapshot_unavailable() for cache consistency after DB updates"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-12
---

# Phase 99 Plan 01-FIX: Availability Tracking Fix Summary

**Fix UAT issues: UnboundLocalError from shadowed import, and stale odds showing as available for events dropped from discovery**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-12
- **Completed:** 2026-02-12
- **Tasks:** 4
- **Files modified:** 3

## Accomplishments

- Fixed UAT-001: Removed redundant local imports that shadowed module-level `update` import
- Fixed UAT-002: Events dropped from discovery now have their markets marked unavailable
- Added DiscoveryResult dataclass to track SR IDs per platform during discovery
- Added reconciliation pass at end of each scrape cycle
- Cache updated alongside DB for immediate API effect

## Task Commits

Each task was committed atomically:

1. **Task 1: Commit UAT-001 fix** - `89fe768` (fix)
2. **Task 2: Track discovered events per platform** - `c5f9fdb` (feat)
3. **Task 3: Add cache reconciliation for missing events** - `610f694` (feat)
4. **Task 4: Update cache to reflect unavailable status** - `2a862ed` (feat)

## Files Created/Modified

- `src/scraping/schemas/coordinator.py` - Added DiscoveryResult dataclass
- `src/scraping/event_coordinator.py` - Modified discover_events() to return DiscoveryResult, added _reconcile_unavailable_events() method
- `src/caching/odds_cache.py` - Added get_cached_events_by_bookmaker(), get_snapshot_for_update(), mark_snapshot_unavailable()

## Decisions Made

- **DB query for SR ID mapping:** During reconciliation, query DB for event_id->sr_id mapping rather than storing SR ID in cache. This avoids invasive changes to CachedSnapshot while keeping reconciliation efficient (single query per cycle).
- **Dual update pattern:** Update DB first, then cache immediately after. This ensures consistency and provides instant API effect without waiting for next scrape.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed plan without issues.

## Next Phase Readiness

Phase 99 FIX complete. UAT-001 and UAT-002 both resolved. Ready for re-verification:

1. Trigger a scrape cycle
2. Check logs for "reconciliation.unavailable_events" message
3. Verify stale competitor data shows as unavailable in UI
4. Verify API returns available=false for stale bookmaker data

---
*Phase: 99-availability-tracking-fix*
*Completed: 2026-02-12*
