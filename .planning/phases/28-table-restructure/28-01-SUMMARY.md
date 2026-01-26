---
phase: 28-table-restructure
plan: 01
subsystem: ui
tags: [react, table, rowspan, odds-comparison]

# Dependency graph
requires:
  - phase: 27-dashboard-coverage-widgets
    provides: existing match table component
provides:
  - bookmakers-as-rows table layout
  - rowspan grouping for match info
  - "Team A - Team B" match name format
affects: [29-double-chance-margins, 30-page-rename-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bookmakers-as-rows layout with rowspan for match grouping"
    - "Market group headers with outcome sub-headers"

key-files:
  created: []
  modified:
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Keep all markets (1X2, O/U 2.5, BTTS) in new row layout"
  - "Use rowspan for Region, Tournament, Kickoff, Match columns"
  - "Match name format: 'Team A - Team B' (single line with hyphen)"

patterns-established:
  - "Bookmakers-as-rows: each match renders N rows (one per bookmaker) with rowspan cells for shared info"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-26
---

# Phase 28 Plan 01: Table Restructure Summary

**Transformed matches table from bookmakers-as-columns to bookmakers-as-rows layout with rowspan grouping for vertical odds comparison**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-26T10:10:00Z
- **Completed:** 2026-01-26T10:18:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 1

## Accomplishments

- Restructured table from horizontal bookmaker columns to vertical bookmaker rows (3 rows per match)
- Implemented rowspan cells for Region, Tournament, Kickoff, Match columns spanning all bookmaker rows
- Changed match name format from two-line "Home Team / vs Away Team" to single-line "Team A - Team B"
- Preserved all markets (1X2, O/U 2.5, BTTS) with market group headers and outcome sub-headers
- Maintained excludeBetpawa support (2 rows for competitor-only view)

## Task Commits

1. **Task 1: Restructure table to bookmakers-as-rows layout** - `0b005ce` (feat)

**Plan metadata:** TBD (this commit)

## Files Created/Modified

- `web/src/features/matches/components/match-table.tsx` - Complete restructure of table rendering logic with rowspan layout

## Decisions Made

- **Keep all markets:** Initially simplified to 1X2 only per plan, but restored O/U 2.5 and BTTS based on user feedback
- **Market group headers:** Added two-row header structure with market labels (1X2, O/U 2.5, BTTS) and outcome sub-headers (1, X, 2, Over, Under, Yes, No)
- **Rowspan structure:** First 4 columns (Region, Tournament, Kickoff, Match) span all bookmaker rows vertically

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Restored O/U 2.5 and BTTS markets**
- **Found during:** Checkpoint verification
- **Issue:** Plan specified removing O/U and BTTS markets, but user expected them to remain
- **Fix:** Restored full MARKET_CONFIG with all three markets, added market group headers
- **Files modified:** web/src/features/matches/components/match-table.tsx
- **Verification:** User approved table with all markets visible
- **Committed in:** 0b005ce (amended)

---

**Total deviations:** 1 auto-fixed (user-directed correction)
**Impact on plan:** Minor scope adjustment to preserve existing functionality

## Issues Encountered

None

## Next Phase Readiness

- Table restructure complete with bookmakers-as-rows layout
- Ready for Phase 29: Double Chance & Margins (add 1X, X2, 12 columns and per-market margins)

---
*Phase: 28-table-restructure*
*Completed: 2026-01-26*
