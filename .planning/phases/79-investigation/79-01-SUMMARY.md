---
phase: 79-investigation
plan: 01
subsystem: historical-data
tags: [investigation, bug-analysis, specifiers]
status: complete
duration: ~15 minutes
started: 2026-02-10T14:00:00Z
completed: 2026-02-10T14:15:00Z
tasks_total: 2
tasks_completed: 2
files_created: 1
commits: 2
---

# Phase 79 Plan 01: Investigation Summary

**Root cause identified: History API filters by market_id only, missing line parameter. Over/Under and Handicap markets mix 5-8 different line values in chart data.**

## Performance
- Duration: ~15 minutes
- Started: 2026-02-10T14:00:00Z
- Completed: 2026-02-10T14:15:00Z
- Tasks: 2
- Files created: 1

## Accomplishments

- **SQL Evidence Gathered:** Ran 6 queries demonstrating the bug exists in production data
  - Event 2610 returns 770 rows mixing 5 corner lines (7.5, 8.5, 9.5, 10.5, 11.5)
  - Same market_id stores 8+ different line values correctly in database
  - Current WHERE clause in `history.py` filters by `market_id` only, not `line`

- **Root Cause Traced:** Documented exact file locations where line parameter is missing
  - Backend: `src/api/routes/history.py` lines 253, 273 (query construction)
  - Frontend: `history-dialog.tsx` props, `use-odds-history.ts` params, `api.ts` client
  - Callers: `market-grid.tsx` and `match-table.tsx` don't pass line to dialog

- **Fix Approach Defined:** 6-step implementation plan for Phase 80
  1. Add `line` query param to backend API
  2. Add `line` prop to HistoryDialog
  3. Add `line` to useOddsHistory hook
  4. Add `line` to useMarginHistory hook
  5. Add `line` to API client methods
  6. Update callers to pass line value

- **Files List Created:** 9 files identified requiring changes (1 backend, 8 frontend)

## Task Commits

1. **Task 1: SQL verification** - `f6f1052` (chore)
2. **Task 2: Bug report documentation** - `7599338` (docs)

## Files Created/Modified

- `.planning/phases/79-investigation/BUG-REPORT.md` - Complete bug analysis (404 lines)

## Decisions Made

- **Investigation Scope:** Focused on Over/Under and Handicap markets as primary examples; same bug affects all specifier-based markets
- **Evidence Format:** Used actual database queries rather than hypothetical examples to prove bug exists
- **Fix Approach:** Chose optional `line` parameter (backward compatible) over breaking API change

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - database accessible via Docker, all code paths found as documented in plan.

## Key Findings

| Metric | Value |
|--------|-------|
| Markets affected | All with `line` column (Over/Under, Handicap, Corners, Bookings) |
| Example mixed rows | 770 rows for 154 snapshots (5 lines mixed) |
| Backend changes | 1 file, 2 endpoints, ~10 lines |
| Frontend changes | 8 files, ~50 lines total |

## Next Step

Ready for **Phase 80: Specifier Bug Fix** - Implement the line parameter across the stack.
