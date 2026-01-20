---
phase: 02-database-schema
plan: 02
subsystem: database
tags: [sqlalchemy, postgresql, jsonb, time-series, odds]

# Dependency graph
requires:
  - phase: 02-database-schema/01
    provides: Base class, async engine, core entity models (Sport, Tournament, Bookmaker, Event, EventBookmaker)
provides:
  - OddsSnapshot model with BigInteger PK for partitioning support
  - MarketOdds model with JSONB outcomes storage
  - ScrapeRun model for operational tracking
  - ScrapeError model for failure logging
  - ScrapeStatus StrEnum with 5 states
affects: [02-database-schema/03, 03-scraper-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [BigInteger PK for partitioned tables, JSONB for variable-structure data, StrEnum for status fields]

key-files:
  created: [src/db/models/odds.py, src/db/models/scrape.py]
  modified: [src/db/models/__init__.py]

key-decisions:
  - "BigInteger for snapshot/market IDs to support future partitioning"
  - "JSONB (via JSON type) for raw_response and outcomes to handle variable API structures"
  - "Separate ScrapeRun/ScrapeError models for operational monitoring"

patterns-established:
  - "BigInteger PK: Use for tables that will be partitioned by timestamp"
  - "JSONB storage: Use for variable-structure data like API responses and outcome arrays"
  - "StrEnum: Use for status fields that need both type safety and string storage"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-20
---

# Phase 02-02: Odds Snapshot Models Summary

**Time-series OddsSnapshot/MarketOdds models with BigInteger PKs for partitioning, plus ScrapeRun/ScrapeError for operational monitoring**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-20T00:00:00Z
- **Completed:** 2026-01-20T00:08:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- OddsSnapshot model with BigInteger PK, event/bookmaker FKs, JSONB raw_response, proper indexes
- MarketOdds model with normalized market fields and JSONB outcomes array
- ScrapeRun model tracking scrape executions with status, timing, counts
- ScrapeError model logging failures with error type, message, context
- ScrapeStatus StrEnum with 5 states (pending, running, completed, partial, failed)
- All 11 models exportable from src.db.models package

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OddsSnapshot and MarketOdds models** - `5b4535d` (feat)
2. **Task 2: Create ScrapeRun and ScrapeError models** - `590f827` (feat)

**Plan metadata:** `2080bfc` (docs: complete odds snapshot models plan)

## Files Created/Modified
- `src/db/models/odds.py` - OddsSnapshot and MarketOdds models with indexes
- `src/db/models/scrape.py` - ScrapeRun, ScrapeError models and ScrapeStatus enum
- `src/db/models/__init__.py` - Updated exports for all 11 models

## Decisions Made
- Used BigInteger for snapshot and market odds PKs to support future PostgreSQL partitioning
- Used JSON type (maps to JSONB on PostgreSQL) for raw_response and outcomes fields
- ScrapeStatus as StrEnum following Python 3.11+ pattern for type-safe string enums
- Indexes defined in __table_args__ for common query patterns (event lookup, time-based queries)

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- All SQLAlchemy models defined and importable
- Ready for Alembic migration setup in Plan 03
- Schema supports partitioning (BigInteger PKs), indexes defined for migration to apply
- BRIN index on captured_at will be added via raw SQL in migration

---
*Phase: 02-database-schema*
*Completed: 2026-01-20*
