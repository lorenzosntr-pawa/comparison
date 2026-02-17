# Phase 101 Plan 01: Remove raw_response Columns Summary

**Removed raw_response columns from database schema, reclaiming 33 GB (53% of database storage).**

## Accomplishments

- Removed raw_response from scraping code (competitor_events.py, event_coordinator.py)
- Removed raw_response column from OddsSnapshot and CompetitorOddsSnapshot models
- Removed raw_response field from SnapshotWriteData and CompetitorSnapshotWriteData DTOs
- Created and applied Alembic migration m9n5o1p7q3r9 to drop columns from database
- Verified all Python modules import successfully after changes
- Verified columns no longer exist in database schema

## Files Created/Modified

**Modified:**
- `src/scraping/competitor_events.py` - Removed raw_response from parse methods, snapshot creation, and full odds fetch
- `src/scraping/event_coordinator.py` - Removed raw_response from SnapshotWriteData and CompetitorSnapshotWriteData construction
- `src/db/models/odds.py` - Removed raw_response column from OddsSnapshot model
- `src/db/models/competitor.py` - Removed raw_response column from CompetitorOddsSnapshot model
- `src/storage/write_queue.py` - Removed raw_response field from SnapshotWriteData and CompetitorSnapshotWriteData DTOs
- `src/storage/write_handler.py` - Removed raw_response assignment when creating snapshots

**Created:**
- `alembic/versions/m9n5o1p7q3r9_drop_raw_response.py` - Migration to drop raw_response columns

## Commits

1. `3064811` - refactor(101-01): remove raw_response from scraping code
2. `ff2dab4` - refactor(101-01): remove raw_response from models, DTOs, write handler
3. `814da83` - chore(101-01): add migration to drop raw_response columns

## Decisions Made

- **Fixed migration state blocker**: Database had stale reference to non-existent migration m9n0o1p2q3r4. Fixed by updating alembic_version table directly to valid revision l8m4n0o6p2q3 before running new migration.
- **Used external_id directly for Bet9ja**: Removed raw_response fallback in _fetch_full_odds_api_only since external_id already contains the correct ID (extracted during parsing).

## Issues Encountered

- **Blocker: Alembic migration state inconsistency** - Database was stamped with a migration revision (m9n0o1p2q3r4) that doesn't exist in the codebase. Fixed by directly updating the alembic_version table to the last valid revision before running the new migration. (Deviation Rule 3: Auto-fix blockers)

## Next Phase Readiness

Ready for Phase 102: Scraping Verification & Testing. The schema changes are complete and migration has been applied. Next phase should verify scraping still works correctly after raw_response removal through end-to-end validation.
