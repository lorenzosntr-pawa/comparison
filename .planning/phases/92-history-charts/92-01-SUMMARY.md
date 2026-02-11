---
phase: 92-history-charts
plan: 01
subsystem: ui
tags: [recharts, availability, dashed-lines, history-api]

requires:
  - phase: 91-event-details-ui
    provides: Availability styling patterns
provides:
  - History API with availability fields
  - Chart components with dashed unavailable segments
affects: []

tech-stack:
  added: []
  patterns:
    - "Dashed line overlay for unavailable periods in recharts"
    - "Dual-line rendering: solid=available, dashed=unavailable"
    - "splitByAvailability helper for segment separation"

key-files:
  created: []
  modified:
    - src/api/routes/history.py
    - src/matching/schemas.py
    - web/src/types/api.ts
    - web/src/features/matches/components/odds-line-chart.tsx
    - web/src/features/matches/components/margin-line-chart.tsx

key-decisions:
  - "Dashed overlay approach vs gradient masking: simpler, works without SVG complexity"
  - "splitByAvailability helper to separate data into available/unavailable segments"

patterns-established:
  - "available/unavailable_at fields in history API responses"
  - "Dual-line chart rendering for availability visualization"
  - "Tooltip suffix pattern: (unavailable) appended to values"

issues-created: []

duration: 8min
completed: 2026-02-11
---

# Phase 92 Plan 01: History Charts Availability Summary

**Dashed line visualization for unavailable periods in OddsLineChart and MarginLineChart with availability fields in history API**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-11T14:30:00Z
- **Completed:** 2026-02-11T14:38:00Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Added `available` and `unavailable_at` fields to OddsHistoryPoint and MarginHistoryPoint schemas
- History API endpoints extract availability state using getattr pattern for safe competitor access
- OddsLineChart renders dual lines: solid for available, dashed (strokeDasharray="5 5") for unavailable
- MarginLineChart follows same pattern with availability-aware line rendering
- Both charts show "(unavailable)" suffix in tooltips for unavailable points
- Legend note explains dashed line meaning in both components

## Task Commits

Each task was committed atomically:

1. **Task 1: Add availability fields to history API** - `6b578d1` (feat)
2. **Task 2: Add availability types to history interfaces** - `fc68076` (feat)
3. **Task 3: Visualize availability in OddsLineChart** - `09e83bb` (feat)
4. **Task 4: Visualize availability in MarginLineChart** - `e8d8853` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

- `src/matching/schemas.py` - Added available/unavailable_at to OddsHistoryPoint and MarginHistoryPoint
- `src/api/routes/history.py` - Extract availability from MarketOdds using getattr pattern
- `web/src/types/api.ts` - Added optional available/unavailable_at to history point interfaces
- `web/src/features/matches/components/odds-line-chart.tsx` - Dual-line rendering with splitByAvailability helper
- `web/src/features/matches/components/margin-line-chart.tsx` - Same dual-line pattern for margin charts

## Decisions Made

- Used splitByAvailability helper to separate data points into available/unavailable segments
- Dashed lines use strokeDasharray="5 5" for clear visual distinction
- Tooltip shows "(unavailable)" suffix rather than separate field for cleaner UX
- Both single and comparison modes support availability visualization

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 92 complete, v2.5 Odds Availability Tracking milestone is 100% done
- All 6 phases (87-92) complete
- Ready for `/gsd:complete-milestone`

---
*Phase: 92-history-charts*
*Completed: 2026-02-11*
