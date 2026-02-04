---
phase: 51-navigation-ux
plan: 01-FIX
subsystem: ui
tags: [react, scroll, sticky, navigation, fix]

# Dependency graph
requires:
  - phase: 51-01
    provides: Sticky navigation implementation (broken due to wrong scroll container)
provides:
  - Fixed sticky navigation header
  - Working scroll-to-top button
  - Correct scroll container targeting pattern
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "data-scroll-container attribute for targeting correct scroll element in nested main elements"

key-files:
  created: []
  modified:
    - web/src/components/layout/app-layout.tsx
    - web/src/features/matches/components/market-grid.tsx

key-decisions:
  - "Use data attribute instead of semantic selector to avoid ambiguity with nested main elements"
  - "Position scroll-to-top button at bottom-20 to avoid overlap with API icon"

patterns-established:
  - "data-scroll-container: Use this attribute to target the app's scrollable container from any component"

issues-created: []

# Metrics
duration: 6min
completed: 2026-02-04
---

# Phase 51 Plan 01-FIX: Sticky Navigation Fix Summary

**Fixed scroll container targeting - sticky header and scroll-to-top button now work correctly by querying [data-scroll-container] instead of 'main'**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-04T14:00:00Z
- **Completed:** 2026-02-04T14:06:00Z
- **Tasks:** 3 (+ 1 verification checkpoint)
- **Files modified:** 2

## Accomplishments

- Fixed sticky navigation header (UAT-001) - now stays fixed at top when scrolling
- Fixed scroll-to-top button appearance (UAT-002) - now shows after scrolling 400px
- Fixed button position conflict (UAT-003) - moved from bottom-6 to bottom-20
- Fixed layout shift (UAT-004) - placeholder pattern now works correctly
- Fixed shadow effect (UAT-005) - shadow appears when header is stuck

## Task Commits

1. **Task 1: Add data-scroll-container attribute** - `5ff2367` (fix)
2. **Tasks 2-3: Fix scroll listener and button position** - `f368261` (fix)

**Plan metadata:** This commit (docs: complete plan)

## Files Created/Modified

- `web/src/components/layout/app-layout.tsx` - Added `data-scroll-container` attribute to inner main element
- `web/src/features/matches/components/market-grid.tsx` - Updated all `querySelector('main')` calls to use `[data-scroll-container]`, moved button from bottom-6 to bottom-20

## Decisions Made

- Used data attribute (`data-scroll-container`) instead of more specific CSS selector to make the pattern clear and reusable
- Positioned button at bottom-20 (80px) to clear the API icon area in bottom-right corner

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Root Cause Analysis

The original 51-01 implementation failed because:
1. App has two nested `<main>` elements (SidebarInset renders as `<main>`, and app-layout has inner `<main>`)
2. `document.querySelector('main')` returns the first (outer) one, which is not the scroll container
3. All scroll-related logic attached to wrong element, so scroll events never fired

Fix: Added `data-scroll-container` attribute to the correct (inner) main and updated all queries.

## Next Phase Readiness

- All UAT issues resolved
- Phase 51 fully complete
- Ready for Phase 52: Polish & Integration

---
*Phase: 51-navigation-ux*
*Completed: 2026-02-04*
