---
phase: 04-event-matching
plan: 01
subsystem: database
tags: [sqlalchemy, postgresql, upsert, pydantic, event-matching]

# Dependency graph
requires:
  - phase: 02-database-schema
    provides: Event, Tournament, EventBookmaker models with sportradar_id
  - phase: 03-scraper-integration
    provides: Platform enum, _get_bookmaker_id pattern
provides:
  - EventMatchingService with atomic upsert methods
  - ProcessingResult, MatchedEvent, UnmatchedEvent schemas
  - Bulk lookup by sportradar_id for O(1) event matching
affects: [04-02, 05-scheduled-scraping, 07-match-views]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - insert().on_conflict_do_update() for PostgreSQL atomic upserts
    - Betpawa-first metadata priority pattern
    - Bulk fetch with IN clause for O(1) lookup

key-files:
  created:
    - src/matching/__init__.py
    - src/matching/service.py
    - src/matching/schemas.py
  modified: []

key-decisions:
  - "Betpawa-first: Betpawa updates metadata, competitors insert-only (except kickoff)"
  - "Combined Task 1 and Task 2 into single commit - schemas were service dependency"

patterns-established:
  - "insert().on_conflict_do_update(index_elements=[...]) for sportradar_id upserts"
  - "on_conflict_do_nothing for competitor tournament metadata (don't overwrite Betpawa)"
  - "Tournament cache dict in process_scraped_events for batch efficiency"

issues-created: []

# Metrics
duration: 3min
completed: 2026-01-20
---

# Phase 4 Plan 1: Event Matching Service Summary

**EventMatchingService with PostgreSQL atomic upserts and Betpawa-first metadata priority for cross-platform event matching**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-20T13:41:00Z
- **Completed:** 2026-01-20T13:44:31Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- EventMatchingService with upsert_tournament, upsert_event, upsert_event_bookmaker methods
- PostgreSQL INSERT...ON CONFLICT DO UPDATE for atomic upserts
- Betpawa-first metadata priority (Betpawa updates all fields, competitors only update kickoff)
- Bulk fetch by sportradar_id IN (...) for O(1) lookup
- ProcessingResult, MatchedEvent, UnmatchedEvent, BookmakerOdds, MatchedEventList schemas

## Task Commits

1. **Task 1-2: Event matching service + schemas** - `d45a637` (feat)
   - Combined commit: service required schemas as import dependency

**Plan metadata:** (this commit)

## Files Created/Modified

- `src/matching/__init__.py` - Module exports EventMatchingService
- `src/matching/service.py` - EventMatchingService with all upsert methods
- `src/matching/schemas.py` - Pydantic schemas for API responses

## Decisions Made

- Combined Task 1 and Task 2 into single commit since service imports ProcessingResult from schemas
- Used constraint name "uq_event_bookmaker" for EventBookmaker upsert (matches existing model)
- Tournament fallback: when no sportradar_id, use name+sport_id for matching

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- EventMatchingService ready for integration with scraping orchestrator
- Ready for 04-02-PLAN.md (orchestrator integration)

---
*Phase: 04-event-matching*
*Completed: 2026-01-20*
