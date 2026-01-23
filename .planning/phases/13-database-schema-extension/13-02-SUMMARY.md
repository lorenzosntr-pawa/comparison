---
phase: 13-database-schema-extension
plan: 02
subsystem: database
tags: [alembic, postgresql, sqlalchemy, migration]

# Dependency graph
requires:
  - phase: 13-01
    provides: Competitor models (CompetitorTournament, CompetitorEvent, etc.)
provides:
  - ScrapeBatch model for grouping platform scrape runs
  - Alembic migration for all Phase 13 tables
  - Database schema ready for competitor scraping
affects: [phase-14-scraping, phase-15-full-events, phase-18-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ScrapeBatch groups multiple ScrapeRuns by platform"
    - "Nullable batch_id FK for backward compatibility"

key-files:
  created:
    - alembic/versions/91f4cbcafaf2_add_competitor_tables_and_scrape_batches.py
  modified:
    - src/db/models/scrape.py
    - src/db/models/__init__.py

key-decisions:
  - "Made batch_id nullable for backward compatibility with existing scrape_runs"

patterns-established:
  - "ScrapeBatch → ScrapeRun one-to-many relationship for batch visibility"

issues-created: []

# Metrics
duration: 4min
completed: 2026-01-23
---

# Phase 13 Plan 2: Migration Summary

**ScrapeBatch model with Alembic migration creating 5 new tables and batch_id FK on scrape_runs**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-23T15:30:00Z
- **Completed:** 2026-01-23T15:34:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created ScrapeBatch model for grouping platform runs
- Added batch_id FK to ScrapeRun with relationship
- Created comprehensive Alembic migration with all Phase 13 tables
- Applied migration successfully - all 5 new tables created

## Task Commits

1. **Task 1: Create ScrapeBatch model** - `265b526` (feat)
2. **Task 2: Create Alembic migration** - `e91091f` (feat)
3. **Task 3: Apply migration** - No code changes (database operation only)

## Files Created/Modified

- `src/db/models/scrape.py` - Added ScrapeBatch model, batch_id FK and relationship to ScrapeRun
- `src/db/models/__init__.py` - Export ScrapeBatch
- `alembic/versions/91f4cbcafaf2_add_competitor_tables_and_scrape_batches.py` - Migration for all Phase 13 tables

## Database Tables Created

1. **scrape_batches** - Groups platform runs with status, trigger, notes
2. **competitor_tournaments** - Tournaments from SportyBet/Bet9ja with SR ID
3. **competitor_events** - Events with betpawa linkage and SR ID matching
4. **competitor_odds_snapshots** - Point-in-time odds capture
5. **competitor_market_odds** - Individual market odds with outcomes

## Decisions Made

- Made batch_id nullable on scrape_runs for backward compatibility with existing data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 13 complete - database schema fully extended
- All competitor tables ready for Phase 14 scraping
- ScrapeBatch enables batch visibility in UI

---
*Phase: 13-database-schema-extension*
*Completed: 2026-01-23*
