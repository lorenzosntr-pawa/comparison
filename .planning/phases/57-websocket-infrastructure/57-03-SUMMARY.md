---
phase: 57-websocket-infrastructure
plan: 03
subsystem: api
tags: [websocket, asyncio, callback, real-time, cache]

# Dependency graph
requires:
  - phase: 57-02
    provides: WebSocket message protocol and ConnectionManager
  - phase: 54
    provides: OddsCache with put_betpawa_snapshot/put_competitor_snapshot
provides:
  - OddsCache change notification callback mechanism
  - Cache-to-WebSocket bridge for real-time odds updates
  - odds_updates topic broadcasts on cache mutations
affects: [58-websocket-ui-migration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - sync-to-async callback bridge via asyncio.get_running_loop()
    - error-isolated callback iteration

key-files:
  created: []
  modified:
    - src/caching/odds_cache.py
    - src/api/websocket/bridge.py
    - src/api/websocket/__init__.py
    - src/api/app.py

key-decisions:
  - "Sync callbacks with async scheduling - put_*_snapshot methods remain sync"
  - "Single event updates not batched - simplicity over optimization at current scale"
  - "Error isolation per callback - one failure doesn't stop others"

patterns-established:
  - "on_update callback registration pattern for cache mutations"
  - "loop.create_task() for scheduling async work from sync callbacks"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-06
---

# Phase 57 Plan 03: Odds Change Notifications via WebSocket Summary

**OddsCache callback mechanism enables real-time WebSocket broadcasting of odds updates to subscribed clients**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-06T09:55:00Z
- **Completed:** 2026-02-06T10:00:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- OddsCache now fires callbacks on every put_betpawa_snapshot and put_competitor_snapshot call
- Sync callback safely schedules async WebSocket broadcasts via asyncio event loop
- Connected WebSocket clients subscribing to "odds_updates" receive notifications with event_ids and source
- Bridge registered during app lifespan startup after cache and ws_manager initialization
- Error in one callback doesn't prevent others from running

## Task Commits

Each task was committed atomically:

1. **Task 1: Add change notification callback to OddsCache** - `2626ccd` (feat)
2. **Task 2: Wire cache updates to WebSocket broadcasting** - `adab8fe` (feat)

**Plan metadata:** (pending) (docs: complete plan)

## Files Created/Modified

- `src/caching/odds_cache.py` - Added on_update() registration, _notify_update() method, callback invocation in put_*_snapshot
- `src/api/websocket/bridge.py` - Added create_cache_update_bridge() and _safe_broadcast() async helper
- `src/api/websocket/__init__.py` - Export create_cache_update_bridge
- `src/api/app.py` - Register cache bridge in lifespan after ws_manager init

## Decisions Made

- Keep callbacks synchronous (not async) because put_*_snapshot methods are sync - use asyncio.get_running_loop().create_task() to schedule async broadcast
- Single event updates → single WebSocket messages (no batching) - current scale of ~1,300 events across 3 platforms is manageable
- Error isolation: try/except around each callback invocation ensures one failure doesn't affect others
- No deregistration needed - callbacks live for app lifetime

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 57 WebSocket Infrastructure complete
- All 3 plans executed: connection manager (57-01), message protocol + scrape bridge (57-02), odds change notifications (57-03)
- WebSocket clients can now subscribe to:
  - `scrape_progress` - real-time scrape progress updates (parallel to SSE)
  - `odds_updates` - real-time odds change notifications (new capability)
- Ready for Phase 58: WebSocket UI Migration

---
*Phase: 57-websocket-infrastructure*
*Completed: 2026-02-06*
