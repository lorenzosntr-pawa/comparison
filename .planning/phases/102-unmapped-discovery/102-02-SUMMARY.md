---
phase: 102-unmapped-discovery
plan: 02
subsystem: api, websocket
tags: [fastapi, pydantic, websocket, unmapped-markets, crud, alerts]

# Dependency graph
requires:
  - phase: 102-01
    provides: UnmappedLogger service, UnmappedMarketLog model, get_new_markets() method
provides:
  - REST API endpoints for unmapped markets (list, detail, update)
  - WebSocket alerts when new unmapped markets discovered
  - Pydantic schemas for unmapped market API responses
affects: [103-mapping-dashboard, frontend-unmapped-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "WebSocket topic-based alerts for background discoveries"
    - "Optional ws_manager parameter on coordinator for decoupled alerting"

key-files:
  created:
    - src/api/schemas/unmapped.py
    - src/api/routes/unmapped.py
  modified:
    - src/api/app.py
    - src/api/websocket/manager.py
    - src/api/websocket/messages.py
    - src/scraping/event_coordinator.py
    - src/scheduling/jobs.py
    - src/api/routes/scrape.py
    - src/market_mapping/cache.py

key-decisions:
  - "Pass ws_manager as optional parameter to EventCoordinator (like odds_cache and write_queue)"
  - "Broadcast alert after flush, only when new_count > 0 and ws_manager available"
  - "Use camelCase in alert payload for frontend consistency"
  - "Clear new_markets list after alert sent to prevent duplicate alerts"

patterns-established:
  - "Unmapped market API follows existing mapping CRUD patterns"
  - "WebSocket alert message builder follows _envelope() pattern"

issues-created: []

# Metrics
duration: 15 min
completed: 2026-02-13
---

# Phase 102 Plan 02: API Endpoints + WebSocket Alerts Summary

**REST API for unmapped market discovery with WebSocket alerts on new market detection during scraping**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-13T15:00:00Z
- **Completed:** 2026-02-13T15:15:00Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Created Pydantic schemas for unmapped market list/detail/update responses
- Implemented GET /unmapped, GET /unmapped/{id}, PATCH /unmapped/{id} endpoints
- Added "unmapped_alerts" WebSocket topic with build_unmapped_alert() message builder
- Integrated ws_manager into EventCoordinator for real-time alerts after flush
- Fixed import path bug in MappingCache (db.models -> src.db.models)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create unmapped markets API endpoints** - `88e41a6` (feat)
2. **Task 2: Add WebSocket topic and broadcast alerts** - `69da3ec` (feat)

**Plan metadata:** (pending)

## Files Created/Modified

- `src/api/schemas/unmapped.py` - Pydantic schemas for unmapped market API
- `src/api/routes/unmapped.py` - REST endpoints for unmapped market CRUD
- `src/api/app.py` - Router registration
- `src/api/websocket/manager.py` - Added "unmapped_alerts" to TOPICS
- `src/api/websocket/messages.py` - build_unmapped_alert() message builder
- `src/scraping/event_coordinator.py` - ws_manager parameter and alert broadcast
- `src/scheduling/jobs.py` - Pass ws_manager to EventCoordinator
- `src/api/routes/scrape.py` - Pass ws_manager to EventCoordinator (2 places)
- `src/market_mapping/cache.py` - Fixed import path bug

## Decisions Made

- Pass ws_manager as optional parameter to EventCoordinator rather than accessing via global app state
- Broadcast alert only when unmapped_count > 0 and ws_manager is available
- Use camelCase in alert payload (externalMarketId, marketName) for frontend consistency
- Clear new_markets list after alert to prevent duplicate alerts on next flush

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed import path in MappingCache**
- **Found during:** Task 1 (Router import verification)
- **Issue:** MappingCache had incorrect import `from db.models.mapping` instead of `from src.db.models.mapping`
- **Fix:** Changed import to use full src-prefixed path
- **Files modified:** src/market_mapping/cache.py
- **Verification:** Import succeeds, unmapped router loads correctly
- **Committed in:** 88e41a6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (blocking import bug), 0 deferred
**Impact on plan:** Bug fix necessary for correctness. No scope creep.

## Issues Encountered

None.

## Next Phase Readiness

- Unmapped markets API ready for frontend integration
- WebSocket alerts enable real-time notification of new unmapped markets
- Phase 102 complete - ready for Phase 103 Mapping Dashboard

---
*Phase: 102-unmapped-discovery*
*Completed: 2026-02-13*
