---
phase: 63-freshness-timestamps
plan: 01
subsystem: ui, api
tags: [pydantic, react, typescript, timestamps, freshness]

# Dependency graph
requires:
  - phase: 62-historical-data-api
    provides: Historical snapshots with captured_at timestamps
provides:
  - snapshot_time field in BookmakerOdds schema
  - Freshness timestamps visible in Odds Comparison page
  - Freshness timestamps visible in Event Details page
  - formatRelativeTime utility for relative time display
affects: [64-chart-library, 65-history-dialog]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Relative time display (Xm ago, Xh ago) for data freshness

key-files:
  created: []
  modified:
    - src/matching/schemas.py
    - src/api/routes/events.py
    - web/src/types/api.ts
    - web/src/features/matches/lib/market-utils.ts
    - web/src/features/matches/components/match-table.tsx
    - web/src/features/matches/components/summary-section.tsx

key-decisions:
  - "Subtle timestamp display (text-xs, muted-foreground) to avoid UI clutter"
  - "Relative time format (2m ago) for quick comprehension"

patterns-established:
  - "formatRelativeTime helper for consistent timestamp display across pages"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-06
---

# Phase 63: Freshness Timestamps Summary

**Added snapshot_time field to BookmakerOdds schema with relative time display ("2m ago") in both Odds Comparison and Event Details pages**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-06
- **Completed:** 2026-02-06
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added snapshot_time field to BookmakerOdds Pydantic schema
- Populated snapshot_time from captured_at in all event API response builders
- Created formatRelativeTime helper for consistent relative time display
- Displayed freshness timestamps in Odds Comparison table (below bookmaker abbreviation)
- Displayed freshness timestamps in Event Details summary section (next to bookmaker name)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add snapshot_time to BookmakerOdds schema and events API** - `d4762ed` (feat)
2. **Task 2: Display freshness timestamps in frontend** - `5bc5315` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `src/matching/schemas.py` - Added snapshot_time field to BookmakerOdds
- `src/api/routes/events.py` - Populated snapshot_time in _build_matched_event, _build_competitor_event_response, _build_event_detail_response
- `web/src/types/api.ts` - Added snapshot_time to BookmakerOdds interface
- `web/src/features/matches/lib/market-utils.ts` - Added formatRelativeTime helper
- `web/src/features/matches/components/match-table.tsx` - Display timestamp below bookmaker label
- `web/src/features/matches/components/summary-section.tsx` - Display timestamp next to bookmaker name in Market Coverage

## Decisions Made
- Used subtle styling (text-xs, muted-foreground) to keep timestamps non-intrusive
- Relative time format ("2m ago", "3h ago") chosen over absolute timestamps for quick comprehension
- Timestamps display in both locations: Odds Comparison list view and Event Details summary

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- Freshness timestamps now visible on all odds displays
- Ready for Phase 64: Chart Library Integration

---
*Phase: 63-freshness-timestamps*
*Completed: 2026-02-06*
