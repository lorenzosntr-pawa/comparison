---
phase: 54-in-memory-cache
plan: 02
subsystem: scraping, caching
tags: [caching, event-coordinator, eviction, structlog, perf-counter]

# Dependency graph
requires:
  - phase: 54-in-memory-cache
    plan: 01
    provides: OddsCache module, snapshot_to_cached helper, warmup from DB
provides:
  - Scrape pipeline populates OddsCache after every batch commit
  - Expired events evicted automatically after each scrape cycle
  - Memory estimate included in cache stats
affects: [54-03 API cache integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [cache population from ORM models after commit, reverse-map lookups for competitor events, piggyback eviction on scrape schedule]

key-files:
  created: []
  modified: [src/scraping/event_coordinator.py, src/scheduling/jobs.py, src/caching/odds_cache.py, src/caching/warmup.py, src/caching/__init__.py]

key-decisions:
  - "snapshot_to_cached_from_models() works with in-memory ORM objects post-flush — avoids re-querying DB"
  - "Reverse-map competitor_event_id -> (sr_id, source) from existing competitor_event_map to find betpawa_event_id"
  - "Eviction piggybacks on scrape schedule — no separate background task, runs once per cycle"
  - "2-hour grace period for eviction: keeps recently started matches visible"

patterns-established:
  - "Cache population from ORM models: extract data from flushed models, convert via snapshot_to_cached_from_models"
  - "Piggyback eviction: lightweight cleanup runs after each scrape cycle"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-05
---

# Phase 54 Plan 02: Pipeline Cache Population & Eviction Summary

**Wire scraping pipeline to populate OddsCache after each batch commit, with automatic eviction of expired events using 2-hour grace period**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-05T13:01:42Z
- **Completed:** 2026-02-05T13:06:42Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- EventCoordinator populates OddsCache after every batch db.commit() with per-snapshot error handling
- snapshot_to_cached_from_models() helper converts flushed ORM objects to frozen CachedSnapshot
- Competitor snapshots mapped back to betpawa_event_id via reverse lookup of competitor_event_map
- Cache update timing (cache_update_ms) included in storage progress events
- Automatic eviction of events >2 hours past kickoff after each scrape cycle
- Memory estimate (estimated_memory_mb) added to cache stats()

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire EventCoordinator to update OddsCache after batch storage** - `291f9ef` (feat)
2. **Task 2: Implement automatic cache eviction for expired events** - `b4e204e` (feat)

## Files Created/Modified
- `src/caching/warmup.py` - Added snapshot_to_cached_from_models() conversion helper
- `src/caching/__init__.py` - Exported snapshot_to_cached_from_models
- `src/scraping/event_coordinator.py` - Added odds_cache param, cache population after commit
- `src/scheduling/jobs.py` - Pass odds_cache to coordinator, evict expired after scrape cycle
- `src/caching/odds_cache.py` - Added estimated_memory_mb to stats()

## Decisions Made
- Used snapshot_to_cached_from_models() that takes explicit fields rather than ORM model to avoid coupling with specific model types
- Built reverse maps (event_id -> sr_id, comp_event_id -> sr_id+source) from existing forward maps to avoid extra DB queries
- Eviction runs in the try block after successful scrape completion, not in finally — avoids evicting during error scenarios
- Memory estimate uses ~200 bytes/market + ~100 bytes/snapshot + ~50 bytes/event heuristic

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- Cache is now populated from both warmup (startup) and scraping pipeline (ongoing)
- Cache stats include memory estimate for monitoring
- Ready for plan 54-03 (API cache integration) to serve cached data instead of DB queries

---
*Phase: 54-in-memory-cache*
*Completed: 2026-02-05*
