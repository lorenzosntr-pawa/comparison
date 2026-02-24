---
phase: 107-write-path-changes
plan: 01
subsystem: database
tags: [dataclass, change-detection, dto, frozen-dataclass]

# Dependency graph
requires:
  - phase: 106-schema-migration
    provides: market_odds_current and market_odds_history table schemas
provides:
  - MarketCurrentWrite and MarketWriteBatch frozen dataclasses for market-level writes
  - classify_market_changes() function for per-market change detection
affects: [108-read-path-cache, write-handler, event-coordinator]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Per-market change detection: compare individual markets instead of entire snapshots"
    - "MarketCurrentWrite.changed flag: determines history INSERT vs confirm-only"

key-files:
  created: []
  modified:
    - src/storage/write_queue.py
    - src/caching/change_detection.py
    - src/caching/__init__.py

key-decisions:
  - "Keep existing snapshot-level DTOs for backward compatibility during migration"
  - "Reuse _normalise_outcomes() for outcome comparison (existing pattern)"
  - "Support both dict and ORM object inputs for flexibility"

patterns-established:
  - "MarketCurrentWrite with changed=True/False per market"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 107 Plan 01: Data Structures & Change Detection Summary

**MarketCurrentWrite and MarketWriteBatch DTOs plus classify_market_changes() for per-market change detection**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T11:55:00Z
- **Completed:** 2026-02-24T12:00:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created MarketCurrentWrite frozen dataclass with event_id, bookmaker_slug, and changed flag
- Created MarketWriteBatch frozen dataclass for batching market writes
- Implemented classify_market_changes() function for per-market change detection
- Maintained backward compatibility with existing snapshot-level DTOs

## Task Commits

Each task was committed atomically:

1. **Task 1: Create market-level DTOs in write_queue.py** - `2b58251` (feat)
2. **Task 2: Implement classify_market_changes() in change_detection.py** - `8627f8b` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/storage/write_queue.py` - Added MarketCurrentWrite and MarketWriteBatch frozen dataclasses
- `src/caching/change_detection.py` - Added classify_market_changes() function
- `src/caching/__init__.py` - Exported classify_market_changes

## Decisions Made

- Keep existing MarketWriteData, SnapshotWriteData, WriteBatch for backward compatibility during Phase 107-108 transition
- Reuse existing _normalise_outcomes() helper for outcome comparison (proven pattern)
- Support both dict and ORM object inputs for maximum flexibility with different code paths

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- MarketCurrentWrite and MarketWriteBatch DTOs ready for write handler integration
- classify_market_changes() ready for event_coordinator to use
- Ready for 107-02-PLAN.md: Write Handler & Integration

---
*Phase: 107-write-path-changes*
*Completed: 2026-02-24*
