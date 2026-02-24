---
phase: 106-schema-migration
plan: 01
subsystem: database
tags: [postgresql, alembic, sqlalchemy, partitioning, jsonb]

# Dependency graph
requires:
  - phase: 105-investigation-schema-design
    provides: Schema design with UPSERT current table and partitioned history table
provides:
  - market_odds_current table with COALESCE unique index
  - market_odds_history partitioned table with monthly partitions
  - MarketOddsCurrent and MarketOddsHistory ORM models
affects: [107-write-path, 108-read-path, 109-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - COALESCE in unique constraint for NULL handling
    - PARTITION BY RANGE for monthly history partitions
    - Unified bookmaker_slug column for BetPawa + competitors

key-files:
  created:
    - alembic/versions/n8o7p0q1r4s5_add_market_level_tables.py
    - src/db/models/market_odds.py
  modified:
    - src/db/models/__init__.py

key-decisions:
  - "Used COALESCE(line, 0) in unique constraint for NULL line handling"
  - "Partitioned captured_at as part of composite primary key for PostgreSQL partitioning requirements"
  - "Created 3 monthly partitions upfront (2026_02, 2026_03, 2026_04)"

patterns-established:
  - "Expression-based unique index with COALESCE for nullable columns"
  - "Monthly partitioning by timestamp column"
  - "Unified storage for multiple bookmakers via bookmaker_slug"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-24
---

# Phase 106 Plan 01: Schema Migration Summary

**Created market_odds_current (UPSERT) and market_odds_history (partitioned) tables with SQLAlchemy models for 95% storage reduction architecture**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-24T11:40:00Z
- **Completed:** 2026-02-24T11:52:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Migration file created with market_odds_current table (14 columns, 5 indexes including COALESCE unique)
- market_odds_history partitioned table with 3 monthly partitions (2026_02, 2026_03, 2026_04)
- SQLAlchemy ORM models MarketOddsCurrent and MarketOddsHistory following existing patterns
- Verified UPSERT works correctly with ON CONFLICT COALESCE expression
- Verified partition routing places rows in correct monthly partition

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Alembic migration** - `de29a74` (feat)
2. **Task 2: Create SQLAlchemy ORM models** - `ee8217d` (feat)
3. **Task 3: Verify schema correctness** - No commit (verification only, no files changed)

## Files Created/Modified

- `alembic/versions/n8o7p0q1r4s5_add_market_level_tables.py` - Alembic migration with partitioned tables
- `src/db/models/market_odds.py` - MarketOddsCurrent and MarketOddsHistory ORM models
- `src/db/models/__init__.py` - Export new models

## Decisions Made

1. **COALESCE(line, 0) in unique constraint** - PostgreSQL requires non-NULL values in unique constraints. Using COALESCE allows NULL lines to be treated as 0 for uniqueness purposes.

2. **Composite primary key for history table** - PostgreSQL partitioning requires the partition key (captured_at) to be part of the primary key. Used (id, captured_at) composite key.

3. **Raw SQL for partitioning and expression indexes** - Alembic op helpers don't support PARTITION BY or expression-based indexes directly, so used op.execute() for these features.

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

- **Database had invalid alembic_version** - The database contained revision 'c4d5e6f7g8h9' which didn't exist in version history. Fixed by updating to 'a41eec60ab32' (the actual latest migration) before running the new migration.

## Next Phase Readiness

- Phase 107 ready: Write path changes can begin
- Tables created and verified: market_odds_current, market_odds_history
- Old tables preserved for rollback: odds_snapshots, market_odds, competitor_odds_snapshots, competitor_market_odds
- UPSERT and partition INSERT both working correctly

---
*Phase: 106-schema-migration*
*Completed: 2026-02-24*
