---
phase: 54-in-memory-cache
plan: 01
subsystem: api
tags: [caching, fastapi, dataclass, structlog, sqlalchemy]

# Dependency graph
requires:
  - phase: 53-investigation-benchmarking
    provides: baseline metrics showing API p50=903ms justifying cache layer
provides:
  - OddsCache module with in-memory storage for latest odds snapshots
  - Startup warmup populating cache from DB for upcoming events
  - Cache registered in app.state for downstream API/pipeline access
affects: [54-02 cache population, 54-03 API cache integration, 55 async write pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [frozen dataclass for cache entries, duck-type compatible cache objects, startup warmup from DB]

key-files:
  created: [src/caching/__init__.py, src/caching/odds_cache.py, src/caching/warmup.py]
  modified: [src/api/app.py]

key-decisions:
  - "Frozen dataclasses instead of SQLAlchemy models — avoids detached instance issues with async sessions"
  - "Duck-type compatible CachedSnapshot/CachedMarket — no adapter layer needed, works directly with existing _build_inline_odds()"
  - "Warmup queries upcoming events (kickoff > now - 2h) to include recently started events"

patterns-established:
  - "Frozen dataclass cache entries: immutable, hashable, no ORM session dependency"
  - "Cache warmup in app lifespan: async DB load with perf_counter timing"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-05
---

# Phase 54 Plan 01: Cache Module & Startup Warmup Summary

**OddsCache module with frozen dataclass entries, dict-based lookup by event/bookmaker, and startup warmup from DB via async session**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-05T13:07:48Z
- **Completed:** 2026-02-05T13:12:25Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- OddsCache class with dict-based storage for BetPawa and competitor snapshots
- Frozen dataclass entries (CachedMarket, CachedSnapshot) duck-type compatible with ORM models
- Startup warmup loads latest snapshots for all upcoming events from DB
- Cache registered in app.state with perf_counter timing logged

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OddsCache module with data structures and lookup API** - `435685c` (feat)
2. **Task 2: Implement startup warmup and register cache in app lifespan** - `9264826` (feat)

**Plan metadata:** `323d56b` (docs: complete plan)

## Files Created/Modified
- `src/caching/__init__.py` - Package init exporting OddsCache, CachedSnapshot, CachedMarket
- `src/caching/odds_cache.py` - Full cache implementation with lookup/mutation/stats methods
- `src/caching/warmup.py` - warm_cache_from_db() and snapshot_to_cached() conversion helper
- `src/api/app.py` - Added cache creation, warmup call, and timing in lifespan

## Decisions Made
- Used frozen dataclasses instead of SQLAlchemy models to avoid detached instance issues with async sessions
- CachedSnapshot/CachedMarket duck-type compatible with OddsSnapshot/CompetitorOddsSnapshot — no adapter layer needed
- Warmup queries events with kickoff > now - 2 hours to include recently started events

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- OddsCache is ready for plan 54-02 (scrape pipeline cache population + eviction)
- Cache API matches return signatures of existing DB query functions for seamless integration in plan 54-03

---
*Phase: 54-in-memory-cache*
*Completed: 2026-02-05*
