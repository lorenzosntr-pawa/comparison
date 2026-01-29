---
phase: 40-concurrency-tuning-metrics
plan: 01
subsystem: scraping
tags: [settings, concurrency, metrics, eventcoordinator, api]

# Dependency graph
requires:
  - phase: 39-batch-db-storage
    provides: EventScrapeStatus model, store_batch_results method
provides:
  - Configurable scraping tuning via Settings API
  - EventCoordinator.from_settings() factory method
  - GET /api/scrape/event-metrics endpoint for new flow analytics
affects: [phase-41, scheduler-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Configurable concurrency via Settings singleton
    - Factory method pattern for EventCoordinator initialization

key-files:
  created:
    - alembic/versions/e1f7g5h8i9j0_add_scraping_tuning_settings.py
  modified:
    - src/db/models/settings.py
    - src/api/schemas/settings.py
    - src/scraping/event_coordinator.py
    - src/api/routes/scrape.py
    - src/api/schemas/scheduler.py
    - src/api/schemas/__init__.py
    - src/scraping/schemas/__init__.py

key-decisions:
  - "Added tuning fields to existing Settings model rather than creating separate model"
  - "Used from_settings() factory method to avoid breaking existing EventCoordinator usage"

patterns-established:
  - "Factory method for configurable service initialization"

issues-created: []

# Metrics
duration: 12min
completed: 2026-01-29
---

# Phase 40 Plan 01: Concurrency Tuning & Metrics Summary

**Configurable scraping tuning via Settings API with new event-level metrics endpoint**

## Performance

- **Duration:** 12 min
- **Started:** 2026-01-29T18:45:00Z
- **Completed:** 2026-01-29T18:57:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Added 5 scraping tuning settings to Settings model (betpawa_concurrency, sportybet_concurrency, bet9ja_concurrency, bet9ja_delay_ms, batch_size)
- EventCoordinator now uses configurable concurrency limits and delays via instance attributes
- New GET /api/scrape/event-metrics endpoint provides per-platform success rates and timing analytics from EventScrapeStatus data

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Scraping Tuning Settings to DB and API** - `904a554` (feat)
2. **Task 2: Use Configurable Settings in EventCoordinator** - `310ec46` (feat)
3. **Task 3: Add Event Scrape Metrics API Endpoint** - `cbbc975` (feat)

**Plan metadata:** `02262a4` (docs: complete plan)

## Files Created/Modified

- `alembic/versions/e1f7g5h8i9j0_add_scraping_tuning_settings.py` - Migration for 5 new tuning columns
- `src/db/models/settings.py` - Added tuning columns to Settings model
- `src/api/schemas/settings.py` - Added tuning fields to SettingsResponse and SettingsUpdate
- `src/scraping/event_coordinator.py` - Configurable tuning via __init__ and from_settings() factory
- `src/api/routes/scrape.py` - New GET /api/scrape/event-metrics endpoint
- `src/api/schemas/scheduler.py` - EventMetricsByPlatform and EventScrapeMetricsResponse schemas
- `src/api/schemas/__init__.py` - Export new schemas
- `src/scraping/schemas/__init__.py` - Re-export Platform etc. from parent schemas.py

## Decisions Made

- Added tuning fields directly to existing Settings model (keeps single source of truth)
- Used factory method from_settings() to create EventCoordinator from Settings (non-breaking)
- Kept module-level constants as documentation of defaults, instance attributes for actual limits

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed schemas/ package shadowing schemas.py**
- **Found during:** Task 3 (Event metrics endpoint implementation)
- **Issue:** `src/scraping/schemas/` directory shadowed `src/scraping/schemas.py`, causing `from src.scraping.schemas import Platform` to fail
- **Fix:** Updated `src/scraping/schemas/__init__.py` to dynamically load and re-export Platform, PlatformResult, etc. from the parent schemas.py file
- **Files modified:** src/scraping/schemas/__init__.py
- **Verification:** `from src.api.routes.scrape import router` succeeds
- **Committed in:** cbbc975 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (blocking import issue), 0 deferred
**Impact on plan:** Fix was necessary for app to import correctly. No scope creep.

## Issues Encountered

None - plan executed as specified.

## Next Phase Readiness

- Scraping tuning is now configurable via Settings API
- EventCoordinator can be created from Settings with from_settings()
- Event-level metrics available via GET /api/scrape/event-metrics
- Ready for Phase 41: On-Demand API (POST /api/scrape/{sr_id})

---
*Phase: 40-concurrency-tuning-metrics*
*Completed: 2026-01-29*
