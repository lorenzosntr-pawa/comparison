---
phase: 81-interactive-chart
plan: 01-FIX
subsystem: ui
tags: [recharts, react-hooks, click-handler, state-management]

requires:
  - phase: 81
    provides: click-to-lock chart functionality (broken)
provides:
  - Working click-to-lock on OddsLineChart and MarginLineChart
  - Debounced click handler to prevent rapid-click issues
  - Index-based toggle comparison for reliable state management
affects: [history-dialog, market-history-panel]

tech-stack:
  added: []
  patterns:
    - "Ref-based state tracking for stable callbacks"
    - "Debounce pattern for click handlers (100ms)"
    - "Index comparison over time string comparison"

key-files:
  modified:
    - web/src/features/matches/hooks/use-chart-lock.ts
    - web/src/features/matches/components/odds-line-chart.tsx
    - web/src/features/matches/components/margin-line-chart.tsx

key-decisions:
  - "Use refs to track locked index to avoid stale closure issues"
  - "Debounce clicks at 100ms to prevent double-fire"
  - "Compare indices instead of time strings for toggle logic"

issues-created: []

duration: 8min
completed: 2026-02-10
---

# Phase 81 Plan 01-FIX: Click-to-Lock Fix Summary

**Fixed click-to-lock functionality with debounce, ref-based state, and index comparison**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-10
- **Completed:** 2026-02-10
- **Tasks:** 4 (3 auto + 1 checkpoint)
- **Files modified:** 3

## Accomplishments

- Fixed "brief flash" bug where click-to-lock would immediately unlock
- Added 100ms debounce to prevent rapid click issues
- Used refs to avoid stale closure problems in useCallback
- Added explicit bounds checking to prevent out-of-bounds access

## Task Commits

1. **Tasks 1-3: Fix click-to-lock** - `42959da` (fix)

**Plan metadata:** (this commit)

## Files Created/Modified

- `web/src/features/matches/hooks/use-chart-lock.ts` - Added debounce, refs, index comparison
- `web/src/features/matches/components/odds-line-chart.tsx` - Fixed useEffect deps, bounds checking
- `web/src/features/matches/components/margin-line-chart.tsx` - Same fixes applied

## Root Cause Analysis

The original issue was caused by multiple factors:

1. **Time string comparison** - The original code compared `lockedTime === time` to toggle, but time strings could have subtle format differences
2. **Stale closure** - The `handleChartClick` callback depended on `lockedTime`, creating potential stale closure issues
3. **No debounce** - Rapid clicks (or recharts internal event handling) could fire multiple times

## Fixes Applied

1. **Index-based comparison** - Use `lockedIndexRef.current === index` instead of time comparison
2. **Ref-based tracking** - Track locked index via `useRef` to avoid stale closures
3. **Debounce** - Ignore clicks within 100ms of last click
4. **Bounds checking** - Explicit `lockedIndex < chartData.length` checks
5. **Effect dependencies** - Removed `chartData` from useEffect deps to prevent retriggering

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - fixes worked as expected.

## UAT Issues Resolved

- UAT-001: OddsLineChart click-to-lock doesn't persist - **FIXED**
- UAT-002: MarginLineChart click-to-lock doesn't persist - **FIXED**
- UAT-003: Comparison panel doesn't appear - **FIXED**

## Next Phase Readiness

- All 3 UAT issues resolved
- Charts now properly lock on click with reference line and comparison panel
- Ready to proceed to Phase 82 (Comparison Table)

---
*Phase: 81-interactive-chart*
*Plan: 01-FIX*
*Completed: 2026-02-10*
