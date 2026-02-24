---
phase: 105-investigation-schema-design
plan: 01
subsystem: database
tags: [schema-design, change-detection, storage-optimization, postgresql]

# Dependency graph
requires:
  - phase: 100-investigation-analysis
    provides: Storage profiling, raw_response removal strategy
provides:
  - Market-level schema design (market_odds_current, market_odds_history)
  - Complete write/read path documentation
  - 95% storage reduction strategy
affects: [106-schema-migration, 107-write-path, 108-read-path, 109-historical-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Market-level upsert pattern (UNIQUE constraint on event+bookmaker+market+line)"
    - "Append-only history with monthly partitioning"
    - "Unified BetPawa + competitor storage via bookmaker_slug"

key-files:
  created:
    - .planning/phases/105-investigation-schema-design/DISCOVERY.md
  modified: []

key-decisions:
  - "Snapshot-level change detection is root cause - writes ALL markets when ANY changes"
  - "market_odds_current for API reads (upsert) + market_odds_history for charts (append)"
  - "Unified storage for BetPawa + competitors using bookmaker_slug column"
  - "Monthly partitioning on history table for efficient retention cleanup"
  - "95% storage reduction: 7.2M → 360K rows/day"

patterns-established:
  - "Market-level change detection instead of snapshot-level"
  - "Upsert pattern for current state (ON CONFLICT UPDATE)"
  - "Append-only history for charts (no UPDATE, just INSERT)"

issues-created: []

# Metrics
duration: 15min
completed: 2026-02-24
---

# Phase 105 Plan 01: Investigation & Schema Design Summary

**Snapshot-level change detection writes ALL markets when ANY changes; designed market_odds_current (upsert) + market_odds_history (append) for 95% storage reduction**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-24T09:30:00Z
- **Completed:** 2026-02-24T09:45:00Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Traced complete write path: EventCoordinator → classify_batch_changes → WriteBatch → handle_write_batch
- Identified root cause: `markets_changed()` compares at snapshot level, writing all 50+ markets when any single market changes
- Documented all read paths (events list, event detail, history API) with field usage
- Designed new schema: `market_odds_current` (upsert, ~75K rows total) + `market_odds_history` (append, 360K rows/day)
- Calculated 95% reduction: 7.2M → 360K rows/day for history table

## Task Commits

Each task was committed atomically:

1. **Task 1-3: Document write/read paths and design schema** - `7a4e467` (docs)

**Plan metadata:** _pending_ (docs: complete plan)

_Note: All three tasks completed in single document creation_

## Files Created/Modified

- `.planning/phases/105-investigation-schema-design/DISCOVERY.md` - Full investigation with code references, diagrams, and schema DDL

## Decisions Made

1. **Root cause identified:** Current `classify_batch_changes()` does snapshot-level comparison - any market change triggers full snapshot write (all 50+ markets)

2. **Unified storage for BetPawa + competitors:** Single `market_odds_current` table with `bookmaker_slug` column instead of separate tables. Simplifies queries and maintenance.

3. **UNIQUE constraint on (event_id, bookmaker_slug, market_id, line):** Enables UPSERT pattern for `market_odds_current`. Uses `COALESCE(line, 0)` for NULL line values.

4. **Monthly partitioning on history:** `market_odds_history` partitioned by `captured_at` for efficient time-range queries and retention cleanup.

5. **last_updated_at vs last_confirmed_at distinction:**
   - `last_updated_at` = when odds actually changed
   - `last_confirmed_at` = when last verified (updated every scrape)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - investigation proceeded smoothly with good code documentation.

## Next Phase Readiness

- Phase 106 ready: Schema migration with Alembic
- Tables designed: `market_odds_current`, `market_odds_history`
- Migration complexity: MEDIUM
  - Schema changes are straightforward
  - Data migration can run incrementally
  - Code changes span multiple files but are mechanical
  - Dual-write period enables safe rollback

---
*Phase: 105-investigation-schema-design*
*Completed: 2026-02-24*
