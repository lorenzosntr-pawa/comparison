---
phase: 105-investigation-schema
plan: 01
subsystem: alerting
tags: [risk-monitoring, change-detection, sqlalchemy, websocket]

# Dependency graph
requires:
  - phase: 55
    provides: change_detection.py and classify_batch_changes()
  - phase: 87
    provides: availability_detection.py pattern
provides:
  - Alert detection algorithm design
  - RiskAlert database schema
  - Settings model additions for alert configuration
  - Data flow diagram for detection pipeline
affects: [106, 107, 108, 109, 110, 111]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Alert per outcome (not per market) for granular tracking
    - Direction disagreement detection between bookmakers
    - Severity bands with configurable thresholds (7/10/15%)

key-files:
  created:
    - .planning/phases/105-investigation-schema/DISCOVERY.md
  modified: []

key-decisions:
  - "Integration point: store_batch_results() after classify_batch_changes()"
  - "BigInteger IDs for RiskAlert table (high volume expected)"
  - "Separate alert_retention_days from odds_retention_days"
  - "Direction disagreement always ELEVATED severity"
  - "Availability alerts always WARNING severity"

patterns-established:
  - "Alert detection runs after change detection, before cache update"
  - "RiskAlertData frozen dataclass for DTO pattern"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-19
---

# Phase 105 Plan 01: Investigation & Schema Design Summary

**Alert detection algorithms designed for % changes (three severity bands), direction disagreement between bookmakers, and availability changes; RiskAlert schema with BigInteger IDs and 6 configurable settings fields.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-19T11:30:00Z
- **Completed:** 2026-02-19T11:38:00Z
- **Tasks:** 2
- **Files modified:** 1 created

## Accomplishments

- Identified integration point in `store_batch_results()` after `classify_batch_changes()` and `_detect_and_log_availability_changes()`
- Designed detection algorithms for all three alert types with full pseudocode
- Created complete RiskAlert database schema following existing patterns (BigInteger, Mapped[])
- Defined 6 new Settings fields for alert configuration
- Documented data flow diagram showing detection → WebSocket → persistence pipeline

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: Investigation & Schema Design** - `dea27d6` (docs)

**Plan metadata:** `f71f293` (docs: complete plan)

_Note: Both tasks created content in single DISCOVERY.md file_

## Files Created/Modified

- `.planning/phases/105-investigation-schema/DISCOVERY.md` - Full technical design document with:
  - Integration point analysis
  - Detection algorithm pseudocode for all 3 alert types
  - Data flow diagram
  - RiskAlert SQLAlchemy model
  - Settings model additions
  - Migration file template

## Decisions Made

1. **Integration point:** `store_batch_results()` in `event_coordinator.py` (lines ~1567-1612) — access to both cached and new state, runs after change detection for efficiency

2. **Alert granularity:** One alert per outcome change, not per market — enables tracking specific outcome movements

3. **Direction disagreement severity:** Always ELEVATED — these are inherently concerning regardless of magnitude

4. **Availability alert severity:** Always WARNING — indicates change but not magnitude of risk

5. **Separate alert retention:** `alert_retention_days` independent from `odds_retention_days` — alerts may need longer visibility

6. **BigInteger for alert IDs:** Expected high volume like odds_snapshots table

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Step

Ready for Phase 106: Backend Alert Detection — implement `src/caching/risk_detection.py` with all three detection algorithms.

---
*Phase: 105-investigation-schema*
*Completed: 2026-02-19*
