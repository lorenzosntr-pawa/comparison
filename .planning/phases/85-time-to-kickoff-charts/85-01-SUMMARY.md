---
phase: 85-time-to-kickoff-charts
plan: 01
subsystem: ui
tags: [recharts, time-series, margin-analysis, hooks]

# Dependency graph
requires:
  - phase: 84.2
    provides: useTournamentMarkets hook with market margin data
provides:
  - TimeToKickoffPoint interface for normalized time-axis data
  - BucketStats for time bucket analysis (7d+, 3-7d, 24-72h, <24h)
  - openingMargin/closingMargin/marginDelta on TournamentMarket
  - TimeToKickoffChart component with bucket zone visualization
affects: [86-betpawa-vs-competitor, tournament-detail-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Time-to-kickoff normalization: hoursToKickoff = (capturedAt - kickoffTime) / ms_per_hour"
    - "Time bucket classification: 7d+ (<=-168h), 3-7d (<=-72h), 24-72h (<=-24h), <24h (>-24h)"
    - "ReferenceArea for visual bucket zones on recharts"

key-files:
  created:
    - web/src/features/historical-analysis/components/time-to-kickoff-chart.tsx
  modified:
    - web/src/features/historical-analysis/hooks/use-tournament-markets.ts
    - web/src/features/historical-analysis/components/index.ts

key-decisions:
  - "hoursToKickoff uses negative values (e.g., -72 = 72 hours before kickoff)"
  - "Bucket thresholds: -168h (7d), -72h (3d), -24h boundary points"
  - "ReferenceArea with fillOpacity=0.4 for subtle bucket zone shading"

patterns-established:
  - "formatHoursToKickoff(): converts hours to human-readable (-7d, -3d 12h, -6h, KO)"
  - "getTimeBucket(): classifies hoursToKickoff into time bucket categories"

issues-created: []

# Metrics
duration: 6min
completed: 2026-02-11
---

# Phase 85 Plan 01: Time-to-Kickoff Data & Chart Summary

**Extended useTournamentMarkets hook with time-to-kickoff calculations and created TimeToKickoffChart component with normalized X-axis and visual time bucket zones**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-11T10:30:00Z
- **Completed:** 2026-02-11T10:36:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Extended TournamentMarket interface with openingMargin, closingMargin, marginDelta fields
- Added TimeToKickoffPoint interface with hoursToKickoff for normalized time-axis data
- Implemented time bucket statistics (7d+, 3-7d, 24-72h, <24h) with BucketStats
- Created TimeToKickoffChart component with ReferenceArea bucket zone visualization

## Task Commits

Each task was committed atomically:

1. **Task 1: Enhance useTournamentMarkets with time-to-kickoff data** - `94b86de` (feat)
2. **Task 2: Create TimeToKickoffChart component** - `4ebf32d` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `web/src/features/historical-analysis/hooks/use-tournament-markets.ts` - Added TimeToKickoffPoint, BucketStats, getTimeBucket helper, enhanced TournamentMarket interface
- `web/src/features/historical-analysis/components/time-to-kickoff-chart.tsx` - New chart component with normalized X-axis and bucket zones
- `web/src/features/historical-analysis/components/index.ts` - Export TimeToKickoffChart

## Decisions Made

- Used negative hoursToKickoff values (e.g., -72 = 72h before kickoff) for intuitive left-to-right timeline
- Set bucket boundaries at -168h (7 days), -72h (3 days), -24h for meaningful time segments
- Used ReferenceArea with fillOpacity=0.4 for subtle bucket zone visualization
- Added ReferenceLine at bucket boundaries with dashed style for clear separation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- TimeToKickoffChart ready for integration into tournament detail dialog (Plan 02)
- Data hook provides all necessary opening/closing margin calculations
- Bucket statistics available for summary displays

---
*Phase: 85-time-to-kickoff-charts*
*Completed: 2026-02-11*
