---
phase: 90-odds-comparison-ui
plan: 01
subsystem: ui
tags: [react, typescript, tooltip, availability-tracking, odds-display]

# Dependency graph
requires:
  - phase: 89-api-availability-endpoints
    provides: API returns available/unavailable_since fields on market objects
provides:
  - TypeScript types with availability fields (InlineOdds, MarketOddsDetail)
  - Availability display utilities (formatUnavailableSince, getMarketAvailabilityState)
  - OddsValue component with three-state availability rendering
affects: [91-event-details-ui, 92-history-charts]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Three-state availability rendering: available (normal), unavailable (strikethrough + tooltip), never_offered (plain dash)"
    - "OutcomeOddsResult pattern: return object with odds + availability state from getter"

key-files:
  created: []
  modified:
    - web/src/types/api.ts
    - web/src/features/matches/lib/market-utils.ts
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Optional fields with defaults for backward compatibility (available?: boolean defaults to true)"
  - "Tooltip via radix-ui for unavailable markets showing timestamp"
  - "getOutcomeOdds returns full state object to enable single function call per cell"

patterns-established:
  - "Availability field pattern: available?: boolean, unavailable_since?: string | null"
  - "formatUnavailableSince for consistent tooltip text formatting"
  - "getMarketAvailabilityState for three-state logic centralization"

issues-created: []

# Metrics
duration: 5min
completed: 2026-02-11
---

# Phase 90 Plan 01: Odds Comparison UI Availability Summary

**Added three-state availability display to OddsValue: normal odds, strikethrough with tooltip for unavailable, plain dash for never offered**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-11T16:48:27Z
- **Completed:** 2026-02-11T16:52:58Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `available` and `unavailable_since` fields to InlineOdds and MarketOddsDetail TypeScript interfaces with JSDoc
- Created `formatUnavailableSince()` utility for human-readable tooltip text
- Created `getMarketAvailabilityState()` for three-state logic centralization
- Updated OddsValue component to render unavailable markets with strikethrough dash and tooltip
- Wrapped table with TooltipProvider for radix-ui tooltip support

## Task Commits

Each task was committed atomically:

1. **Task 1: Add availability fields to TypeScript API types** - `1f4c76e` (feat)
2. **Task 2: Create availability display utilities** - `070a8d3` (feat)
3. **Task 3: Update OddsValue component with availability styling** - `fbb8a35` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

- `web/src/types/api.ts` - Added available/unavailable_since fields to InlineOdds and MarketOddsDetail
- `web/src/features/matches/lib/market-utils.ts` - Added formatUnavailableSince and getMarketAvailabilityState utilities
- `web/src/features/matches/components/match-table.tsx` - Updated OddsValue component with availability styling

## Decisions Made

- Used optional fields with defaults (available?: boolean defaults to true via logic) for backward compatibility with existing API responses
- Used radix-ui Tooltip for hover state - consistent with existing UI patterns
- Changed getOutcomeOdds to return full OutcomeOddsResult object instead of just odds for efficiency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation proceeded smoothly.

## Verification Results

- `cd web && npx tsc --noEmit` passes
- `cd web && npm run build` succeeds
- Three availability states render correctly based on code review

## Next Phase Readiness

- Phase 91 (Event Details UI) can use same availability patterns
- MarketOddsDetail already has availability fields for detail page
- formatUnavailableSince and getMarketAvailabilityState utilities available for reuse

---
*Phase: 90-odds-comparison-ui*
*Completed: 2026-02-11*
