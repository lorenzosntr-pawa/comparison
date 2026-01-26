---
phase: 29-double-chance-margins
plan: 01
subsystem: ui
tags: [react, typescript, odds-comparison, margins]

# Dependency graph
requires:
  - phase: 28-table-restructure
    provides: Bookmakers-as-rows table layout with rowspan grouping
provides:
  - Double Chance market (4693) as selectable column
  - Per-market margin display in inline odds
  - Comparative margin color coding (Betpawa vs competitors)
affects: [30-page-rename-polish]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Comparative margin color coding (same logic as odds)
    - Per-market margin columns with border dividers

key-files:
  created: []
  modified:
    - src/matching/schemas.py
    - src/api/routes/events.py
    - web/src/types/api.ts
    - web/src/features/matches/hooks/use-column-settings.ts
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Margin color coding uses comparative logic (vs competitors) not absolute thresholds"
  - "Text color for margins instead of background for readability"
  - "Border dividers between market column groups"

patterns-established:
  - "MarginValue component with comparative color coding"
  - "getMarginComparisonData for Betpawa vs competitor margin analysis"

issues-created: []

# Metrics
duration: 12min
completed: 2026-01-26
---

# Phase 29 Plan 01: Double Chance & Margins Summary

**Double Chance market (1X, X2, 12) as selectable column with per-market margin display and comparative color coding**

## Performance

- **Duration:** 12 min
- **Started:** 2026-01-26
- **Completed:** 2026-01-26
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added Double Chance (4693) to inline markets in backend
- Added margin field to InlineOdds schema with calculation
- Double Chance selectable in column settings (opt-in, not default)
- Per-market margin column displayed after each market's outcomes
- Comparative margin color coding (green = Betpawa lower, red = Betpawa higher)
- Clear border dividers between market column groups

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Double Chance to inline markets and include margin** - `cfa3a64` (feat)
2. **Task 2: Add Double Chance to MARKET_CONFIG and display margins** - `bfc8574` (feat)
3. **Fix: Improve margin readability with text colors** - `0b3db9c` (fix)
4. **Fix: Make margin color coding comparative** - `7e96ee9` (fix)

## Files Created/Modified

- `src/matching/schemas.py` - Added margin field to InlineOdds
- `src/api/routes/events.py` - Added 4693 to INLINE_MARKET_IDS, margin calculation
- `web/src/types/api.ts` - Added margin to InlineOdds interface
- `web/src/features/matches/hooks/use-column-settings.ts` - Added Double Chance to AVAILABLE_COLUMNS
- `web/src/features/matches/components/match-table.tsx` - Added DC to MARKET_CONFIG, MarginValue component, margin columns

## Decisions Made

- Margin color coding uses comparative logic (Betpawa vs best competitor) rather than absolute thresholds
- Text color for margins instead of background color for better readability
- Best margin per market highlighted with bold + underline
- Border dividers between market groups for visual separation

## Deviations from Plan

### Refinements During Verification

1. **User feedback: Text color instead of background** - Changed from bg-color boxes to text colors for readability
2. **User feedback: Comparative color coding** - Changed from absolute thresholds (<3% green, >6% red) to comparative (vs competitors)

Both refinements improved UX based on user verification feedback.

## Issues Encountered

None - plan executed with minor styling refinements during verification.

## Next Phase Readiness

- Double Chance and margins complete
- Ready for Phase 30: Page Rename & Polish

---
*Phase: 29-double-chance-margins*
*Completed: 2026-01-26*
