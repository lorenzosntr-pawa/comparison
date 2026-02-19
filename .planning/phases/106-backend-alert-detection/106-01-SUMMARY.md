---
phase: 106-backend-alert-detection
plan: 01
subsystem: backend
tags: [risk-detection, alerts, odds-monitoring, change-detection]

# Dependency graph
requires:
  - phase: 105-investigation-schema
    provides: Alert detection algorithms and integration point design
provides:
  - Risk detection module with 3 detection algorithms
  - RiskAlertData DTO for alert persistence
  - Detection integration in scraping pipeline
affects: [107-alert-storage, 109-real-time-updates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "detect_risk_alerts orchestrator pattern"
    - "AlertThresholds NamedTuple for configuration"
    - "Inline import pattern for detection module"

key-files:
  created:
    - src/caching/risk_detection.py
  modified:
    - src/storage/write_queue.py
    - src/scraping/event_coordinator.py

key-decisions:
  - "Inline import in store_batch_results() for lazy loading"
  - "Hardcoded thresholds for now, Phase 111 adds settings"
  - "Detection runs after change detection and availability detection"

patterns-established:
  - "detect_risk_alerts() as main orchestrator calling specialized detection functions"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-19
---

# Phase 106 Plan 01: Backend Alert Detection Summary

**Risk detection engine with 3 algorithms (price change, direction disagreement, availability) integrated into scraping pipeline**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-19T14:30:00Z
- **Completed:** 2026-02-19T14:38:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created risk_detection.py module with full algorithm implementation from Phase 105 DISCOVERY.md
- Added AlertType (PRICE_CHANGE, DIRECTION_DISAGREEMENT, AVAILABILITY) and AlertSeverity (WARNING, ELEVATED, CRITICAL) enums
- Implemented detect_price_change_alerts() for % change detection with configurable thresholds
- Implemented detect_direction_disagreement_alerts() for Betpawa vs competitor divergence detection
- Implemented convert_availability_to_alerts() for market suspension/return alerting
- Added RiskAlertData frozen dataclass DTO to write_queue.py
- Integrated detection into event_coordinator.py store_batch_results() after availability detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Create risk detection module and DTOs** - `e31dda7` (feat)
2. **Task 2: Integrate detection into event coordinator** - `eb97a49` (feat)

## Files Created/Modified

- `src/caching/risk_detection.py` - Risk detection module with 3 detection algorithms, enums, and main orchestrator
- `src/storage/write_queue.py` - Added RiskAlertData frozen dataclass DTO (34 lines)
- `src/scraping/event_coordinator.py` - Added detect_risk_alerts() call and logging in store_batch_results()

## Decisions Made

- **Inline import pattern**: Imported detect_risk_alerts inside store_batch_results() to follow existing pattern (like classify_batch_changes)
- **Hardcoded thresholds**: Using AlertThresholds(7.0, 10.0, 15.0) for now; Phase 111 will read from settings
- **Detection placement**: After classify_batch_changes() and _detect_and_log_availability_changes(), before cache update

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Detection module complete and integrated
- Generates RiskAlertData DTOs during scrape cycles
- Ready for Phase 107: Alert Storage & API (schema, persistence, endpoints)

---
*Phase: 106-backend-alert-detection*
*Completed: 2026-02-19*
