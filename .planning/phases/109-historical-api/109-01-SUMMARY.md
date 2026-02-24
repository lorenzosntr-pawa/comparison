---
phase: 109-historical-api
plan: 01
subsystem: api
tags: [history, MarketOddsHistory, migration]

# Dependency graph
requires:
  - phase: 108
    provides: market_odds_current read paths, cache warmup from new schema
provides:
  - History API querying market_odds_history
  - Unified bookmaker handling via bookmaker_slug
affects: [frontend history charts, Historical Analysis page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - MarketOddsHistory query pattern for unified bookmaker access

key-files:
  created: []
  modified:
    - src/api/routes/history.py

key-decisions:
  - "Remove get_snapshot_history endpoint entirely (not used by frontend)"
  - "Return available=True for all history points (no unavailable_at in history table)"
  - "Use market_id as market_name fallback (MarketOddsHistory doesn't store names)"

patterns-established: []

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-24
---

# Phase 109 Plan 01: Historical API Summary

**Migrated history API endpoints to query market_odds_history with unified bookmaker_slug handling, removing deprecated snapshot tables**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-24T10:00:00Z
- **Completed:** 2026-02-24T10:05:00Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Updated get_odds_history endpoint to query MarketOddsHistory directly
- Updated get_margin_history endpoint with same unified query pattern
- Removed deprecated get_snapshot_history endpoint (unused by frontend)
- Removed 201 lines of dual-path query logic (BetPawa vs competitor branches)

## Task Commits

1. **Tasks 1-3: Migrate history API** - `2ae41cb` (feat)
   - All three tasks committed together (single file modification)

**Plan metadata:** Pending

## Files Created/Modified

- `src/api/routes/history.py` - Simplified from 518 to 301 lines (-42%), queries MarketOddsHistory instead of snapshot tables

## Decisions Made

- **Remove get_snapshot_history entirely**: Frontend analysis confirmed endpoint is unused. All history access goes through `/markets/{id}/history` and `/markets/{id}/margin-history`
- **available=True for all history points**: MarketOddsHistory doesn't track unavailable_at field. This is acceptable because history only contains changed records, and availability changes create separate entries
- **Use market_id as market_name fallback**: MarketOddsHistory stores only betpawa_market_id, not the human-readable name. Frontend handles this gracefully

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Ready for Phase 110: Retention, Cleanup & Storage Page Fix
- History API now uses market_odds_history
- All read paths (events, palimpsest, history) migrated to new schema
- Ready to update retention jobs and fix Storage page

---
*Phase: 109-historical-api*
*Completed: 2026-02-24*
