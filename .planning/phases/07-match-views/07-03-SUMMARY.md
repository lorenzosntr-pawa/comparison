---
phase: 07-match-views
plan: 03
subsystem: ui
tags: [react, tanstack-query, tailwind, odds-comparison, match-detail]

# Dependency graph
requires:
  - phase: 07-01
    provides: Events API with odds response structure
  - phase: 07-02
    provides: Match list with inline odds
provides:
  - Match detail view with full market grid
  - Color-coded odds comparison (best/worst)
  - Margin analysis per market
  - Competitive position summary
affects: [08-real-time-updates]

# Tech tracking
tech-stack:
  added: []
  patterns: [three-column-bookmaker-comparison, odds-badge-color-coding, margin-indicator]

key-files:
  created:
    - web/src/features/matches/components/match-header.tsx
    - web/src/features/matches/components/market-grid.tsx
    - web/src/features/matches/components/market-row.tsx
    - web/src/features/matches/components/odds-badge.tsx
    - web/src/features/matches/components/margin-indicator.tsx
    - web/src/features/matches/components/summary-section.tsx
    - web/src/features/matches/hooks/use-match-detail.ts
  modified:
    - web/src/features/matches/index.tsx
    - web/src/features/matches/components/index.ts
    - web/src/features/matches/hooks/index.ts
    - web/src/lib/api.ts
    - web/src/types/api.ts

key-decisions:
  - "Three-column grid layout: Market | Betpawa | SportyBet | Bet9ja"
  - "Color coding: green=best odds, red=worst odds (>3% worse)"
  - "Margin comparison: green=lower margin (better for punter)"
  - "Summary section shows competitive position percentage"

patterns-established:
  - "OddsBadge: reusable odds display with best/worst highlighting"
  - "MarginIndicator: percentage with comparison coloring"
  - "MarketGrid: unified market list from canonical Betpawa taxonomy"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-21
---

# Phase 7 Plan 3: Match Detail View Summary

**Full market comparison grid with three-column bookmaker layout, color-coded odds badges, margin indicators, and competitive position summary**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-21T12:10:00Z
- **Completed:** 2026-01-21T12:18:00Z
- **Tasks:** 2 auto + 1 checkpoint
- **Files modified:** 12

## Accomplishments

- Match detail page with header showing team names, kickoff, tournament
- Market comparison grid displaying all markets in unified rows
- Three-column layout for Betpawa, SportyBet, Bet9ja odds
- Color-coded OddsBadge component (green=best, red=worst)
- MarginIndicator showing per-market margin with comparison coloring
- SummarySection with competitive position percentage

## Task Commits

Each task was committed atomically:

1. **Task 1: Create market comparison grid** - `c40ae14` (feat)
2. **Task 2: Add color-coded odds and margin display** - `fb128de` (feat)

**Plan metadata:** (this commit)

## Files Created/Modified

**New files:**
- `web/src/features/matches/components/match-header.tsx` - Header with team names, kickoff, back button
- `web/src/features/matches/components/market-grid.tsx` - Grid component building unified market list
- `web/src/features/matches/components/market-row.tsx` - Row displaying market across all bookmakers
- `web/src/features/matches/components/odds-badge.tsx` - Odds display with best/worst coloring
- `web/src/features/matches/components/margin-indicator.tsx` - Margin percentage with comparison
- `web/src/features/matches/components/summary-section.tsx` - Competitive position summary
- `web/src/features/matches/hooks/use-match-detail.ts` - TanStack Query hook for detail API

**Modified files:**
- `web/src/features/matches/index.tsx` - Added MatchDetail implementation
- `web/src/features/matches/components/index.ts` - Export new components
- `web/src/features/matches/hooks/index.ts` - Export useMatchDetail
- `web/src/lib/api.ts` - Added getEventDetail method
- `web/src/types/api.ts` - Added EventDetailResponse and related types

## Decisions Made

1. **Three-column grid layout** - Market name column + one column per bookmaker for easy visual comparison
2. **Betpawa as reference taxonomy** - Market list built from Betpawa's markets, competitors mapped in
3. **Green/red color coding** - Best odds highlighted green, significantly worse odds (>3%) shown red
4. **Margin comparison** - Lower margin is better for punter, colored accordingly
5. **Competitive position metric** - "X/Y best odds (Z%)" provides quick overall assessment

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 7 complete - all match views implemented
- Match list view with inline odds (07-02)
- Match detail view with full market grid (07-03)
- Color coding and margin analysis working
- Ready for Phase 8: Real-time Updates (WebSocket integration)

---
*Phase: 07-match-views*
*Completed: 2026-01-21*
