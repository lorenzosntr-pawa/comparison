---
phase: 56-concurrency-tuning
plan: 01
subsystem: scraping, api, settings
tags: [asyncio, concurrency, semaphore, gather, httpx, connection-pool, benchmark]

# Dependency graph
requires:
  - phase: 55-03
    provides: async write pipeline, cache-before-persist, decoupled storage
  - phase: 55.1-01
    provides: bug fixes for Phase 55, odds_cache/write_queue backward compat
  - phase: 53-01
    provides: benchmark baseline (34911ms avg batch scrape, 1461s total pipeline)
provides:
  - Intra-batch concurrent event scraping via asyncio.Semaphore + gather
  - Configurable max_concurrent_events setting (default 10)
  - Tuned HTTP connection pool (200 max, 100 keepalive)
  - Settings API for all concurrency parameters
  - Benchmark verification showing 67% batch scrape improvement
affects: [57-websocket-infrastructure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Event-level Semaphore + asyncio.gather for intra-batch concurrency"
    - "scrape_batch() returns list[dict] instead of AsyncGenerator for parallel-safe collection"
    - "Per-platform semaphores throttle load when events run in parallel"
    - "Settings API exposes all concurrency tuning parameters"

key-files:
  created:
    - alembic/versions/j6k2l8m3n9o4_add_max_concurrent_events.py
    - .planning/phases/56-concurrency-tuning/BENCHMARK-PHASE56.md
  modified:
    - src/scraping/event_coordinator.py
    - src/db/models/settings.py
    - src/api/app.py
    - src/api/routes/settings.py
    - src/api/schemas/settings.py
    - scripts/benchmark_pipeline.py

key-decisions:
  - "asyncio.gather(return_exceptions=True) over TaskGroup — partial failure tolerance, no cascading cancellation"
  - "scrape_batch() refactored to return list[dict] — AsyncGenerator incompatible with concurrent task collection"
  - "Event semaphore (max_concurrent_events=10) + platform semaphores (BP=50, SB=50, B9J=15) — dual-layer throttling"
  - "HTTP pool increased to 200/100 — supports 10 events x 3 platforms with headroom for retries"
  - "Settings update endpoint wired for all 6 concurrency fields — previously only read, never written via API"

patterns-established:
  - "Dual-layer semaphore: event-level controls parallelism, platform-level controls rate limiting"
  - "gather + return_exceptions for batch-level fault isolation"
  - "Configurable concurrency via Settings model + API"

issues-created: []

# Metrics
duration: 20min
completed: 2026-02-05
---

# Phase 56 Plan 01: Concurrency Tuning Summary

**Enabled intra-batch concurrent event scraping (10 parallel) cutting batch scrape time by 67% and total pipeline from 24 min to 8.5 min**

## Performance

- **Duration:** 20 min
- **Started:** 2026-02-05T17:17:00Z
- **Completed:** 2026-02-05T17:37:00Z
- **Tasks:** 3/3
- **Files modified:** 6
- **Files created:** 2

## Accomplishments

- Added `max_concurrent_events` field to Settings model with Alembic migration (default=10)
- Refactored `scrape_batch()` from AsyncGenerator to returning `list[dict]` for parallel-safe progress collection
- Implemented event-level `asyncio.Semaphore` + `asyncio.gather(return_exceptions=True)` for concurrent event processing
- Per-platform semaphores now actively throttle load (BP=50, SB=50, B9J=15) as originally intended
- Increased HTTP connection pool from 100/50 to 200/100 for concurrent request headroom
- Wired all 6 concurrency parameters through Settings API (max_concurrent_events, betpawa_concurrency, sportybet_concurrency, bet9ja_concurrency, bet9ja_delay_ms, batch_size)
- Benchmark verified: 1311 events, 0 failures, no rate limiting errors

## Benchmark Results

| Metric | Phase 53 Baseline | Phase 56 | Change |
|--------|-------------------|----------|--------|
| Avg batch scrape time | 34,911ms | 11,482ms | -67.1% |
| Total pipeline time | 1,461,515ms (24.4 min) | 508,604ms (8.5 min) | -65.2% |
| Throughput (events/sec) | 0.9 | 2.6 | +191.8% |
| Events failed | 0 | 0 | no regression |
| max_concurrent_events | 1 (sequential) | 10 | new |
| HTTP max_connections | 100 | 200 | +100% |

## Task Commits

Each task was committed atomically:

1. **Task 1: Add intra-batch event concurrency to EventCoordinator** - `dc5820c` (feat)
2. **Task 2: Tune HTTP pool and expose concurrency settings API** - `8262531` (feat)
3. **Task 3: Benchmark concurrent scraping improvements** - `bee5a89` (perf)

## Files Created/Modified

- `src/scraping/event_coordinator.py` - Concurrent scrape_batch() with event semaphore + gather, from_settings reads max_concurrent_events
- `src/db/models/settings.py` - Added max_concurrent_events field (default=10)
- `alembic/versions/j6k2l8m3n9o4_add_max_concurrent_events.py` - Migration for new column
- `src/api/app.py` - HTTP pool limits increased to 200/100
- `src/api/routes/settings.py` - Update endpoint handles all concurrency fields
- `src/api/schemas/settings.py` - max_concurrent_events in SettingsResponse and SettingsUpdate
- `scripts/benchmark_pipeline.py` - Phase 56 concurrency metrics, throughput, batch distribution
- `.planning/phases/56-concurrency-tuning/BENCHMARK-PHASE56.md` - Full benchmark report

## Decisions Made

- **asyncio.gather over TaskGroup:** TaskGroup cancels all tasks on first exception, which is too aggressive for scraping (one event failure shouldn't stop the batch). gather(return_exceptions=True) isolates failures.
- **scrape_batch() returns list instead of AsyncGenerator:** When events run in parallel via gather, you can't yield from multiple concurrent async generators. Collecting results in a list and returning is cleaner and compatible with concurrent execution.
- **Dual-layer semaphore design:** Event semaphore (10) controls how many events scrape simultaneously. Platform semaphores (50/50/15) throttle per-API load across all concurrent events. This activates the existing platform semaphores that were previously unused due to sequential processing.
- **HTTP pool 200/100:** 10 concurrent events x 3 platforms = 30 simultaneous requests at peak. With retries and keepalive, 200 max connections provides ample headroom.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed successfully, benchmark shows no rate limiting errors or data quality regressions.

## Next Phase Readiness

- Phase 56 complete -- intra-batch concurrent event scraping fully operational
- Pipeline time reduced from ~24 min to ~8.5 min (65% reduction)
- Throughput increased from 0.9 to 2.6 events/second (192% improvement)
- Per-platform semaphores actively throttling under concurrent load
- Concurrency parameters exposed via API for runtime tuning without restart
- Ready for Phase 57 (WebSocket Infrastructure) or further concurrency optimization

---
*Phase: 56-concurrency-tuning*
*Completed: 2026-02-05*
