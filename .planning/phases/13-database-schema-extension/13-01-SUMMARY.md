---
phase: 13-database-schema-extension
plan: 01
subsystem: database
tags: [sqlalchemy, postgresql, competitor-data, soft-delete]

# Dependency graph
requires:
  - phase: 02-database-schema
    provides: SQLAlchemy 2.0 patterns, Base class, naming conventions
provides:
  - CompetitorSource enum for platform identification
  - CompetitorTournament model with soft delete
  - CompetitorEvent model with SR ID linkage
  - CompetitorOddsSnapshot and CompetitorMarketOdds models
affects: [14-tournament-discovery, 15-full-event-scraping, 16-cross-platform-matching]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Parallel competitor tables (not unified)
    - Soft delete via deleted_at column
    - Optional FK to betpawa events for cross-platform linkage

key-files:
  created:
    - src/db/models/competitor.py
  modified:
    - src/db/models/__init__.py

key-decisions:
  - "Source stored as String(20) for direct enum value storage"
  - "sportradar_id required on CompetitorEvent (primary matching key)"
  - "betpawa_event_id nullable - NULL means competitor-only event"

patterns-established:
  - "Competitor models parallel betpawa models structure"
  - "Partial indexes for nullable columns (sportradar_id, betpawa_event_id)"

issues-created: []

# Metrics
duration: 4min
completed: 2026-01-23
---

# Phase 13 Plan 1: Competitor Models Summary

**SQLAlchemy 2.0 models for storing competitor tournament/event/odds data with SportRadar ID linkage and soft delete support**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-23T16:00:00Z
- **Completed:** 2026-01-23T16:04:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Created CompetitorSource enum (SPORTYBET, BET9JA) for platform identification
- Created CompetitorTournament model with source tracking, external IDs, and soft delete
- Created CompetitorEvent model with SportRadar ID linkage and optional betpawa FK
- Created CompetitorOddsSnapshot and CompetitorMarketOdds for competitor odds storage
- Exported all models from src.db.models package

## Task Commits

All tasks committed atomically (models in single file):

1. **Tasks 1-3: All competitor models** - `7dbb78d` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `src/db/models/competitor.py` - All 5 competitor models: CompetitorSource enum, CompetitorTournament, CompetitorEvent, CompetitorOddsSnapshot, CompetitorMarketOdds
- `src/db/models/__init__.py` - Export all new models

## Decisions Made

- Source column stored as String(20) rather than native Enum for simplicity
- sportradar_id is REQUIRED on CompetitorEvent (this is the primary cross-platform matching key)
- betpawa_event_id is NULLABLE - when NULL, the event exists only on competitor platforms
- Soft delete implemented via deleted_at column on tournaments and events

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- All 5 competitor models created and importable
- Models follow established SQLAlchemy 2.0 patterns from Phase 2
- Ready for Plan 13-02 (Alembic migration creation)

---
*Phase: 13-database-schema-extension*
*Completed: 2026-01-23*
