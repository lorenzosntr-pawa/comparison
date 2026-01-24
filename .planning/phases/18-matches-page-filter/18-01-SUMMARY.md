---
phase: 18-matches-page-filter
plan: 01
subsystem: api, ui
tags: [fastapi, react, filtering, competitor-events, toggle]

# Dependency graph
requires:
  - phase: 17-02
    provides: Palimpsest events endpoint with availability filter
provides:
  - Extended /api/events endpoint with availability filter (betpawa | all)
  - Mode toggle on Matches page for viewing competitor-only events
  - Competitor-only event display with visual indicators
affects: [19-palimpsest-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Negative IDs for competitor-only events to distinguish from BetPawa events"
    - "Button group toggle for mode switching (custom, no external tabs component)"
    - "Metadata priority: sportybet > bet9ja for competitor-only events"

key-files:
  created: []
  modified:
    - src/api/routes/events.py
    - web/src/lib/api.ts
    - web/src/features/matches/index.tsx
    - web/src/features/matches/hooks/use-matches.ts
    - web/src/features/matches/components/match-filters.tsx
    - web/src/features/matches/components/match-table.tsx

key-decisions:
  - "Use negative IDs (-competitor_event.id) for competitor-only events to distinguish from BetPawa events"
  - "Use custom button group instead of shadcn/ui Tabs (component not available)"
  - "Subtle visual indicator: border-l-2 border-l-orange-500/30 for competitor-only events"

patterns-established:
  - "Availability filter pattern for events endpoint (betpawa | all)"

issues-created: []

# Metrics
duration: 6min
completed: 2026-01-24
---

# Phase 18 Plan 01: Event Mode Toggle Summary

**Extended /api/events endpoint with availability filter and added mode toggle to Matches page for viewing competitor-only events alongside BetPawa-matched events**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-24T20:43:44Z
- **Completed:** 2026-01-24T20:49:32Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Extended /api/events endpoint with `availability` query parameter (betpawa | all)
- Competitor-only events include inline odds from CompetitorOddsSnapshot
- Negative IDs distinguish competitor-only events from BetPawa events
- Metadata priority (sportybet > bet9ja) applied for duplicate SR IDs
- Mode toggle button group on Matches page filter row
- Competitor-only events display with subtle visual indicator
- Navigation disabled for competitor-only events (no detail view)

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend /api/events endpoint with availability filter** - `d4fc642` (feat)
2. **Task 2: Add mode toggle to Matches page** - `302222e` (feat)
3. **Task 3: Handle competitor-only events in table** - `307ef59` (feat)

**Plan metadata:** (pending)

## Files Created/Modified

- `src/api/routes/events.py` - Added availability filter, competitor event loading, inline odds for competitors (+311 lines)
- `web/src/lib/api.ts` - Added availability parameter to getEvents
- `web/src/features/matches/index.tsx` - Added availability to DEFAULT_FILTERS and useMatches call
- `web/src/features/matches/hooks/use-matches.ts` - Added availability to params and queryKey
- `web/src/features/matches/components/match-filters.tsx` - Added mode toggle button group
- `web/src/features/matches/components/match-table.tsx` - Added competitor-only event handling

## Decisions Made

- **Negative IDs for competitor events:** Use -competitor_event.id to distinguish from BetPawa events. Frontend can check `event.id < 0` to identify competitor-only events.
- **Custom button group:** shadcn/ui Tabs component not available in project, used custom styled button group with bg-muted styling to match Tabs appearance.
- **Subtle visual indicator:** border-l-2 border-l-orange-500/30 provides visual distinction without being intrusive, per CONTEXT.md requirement that events "feel native".

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing shadcn/ui Tabs component**
- **Found during:** Task 2 (Add mode toggle)
- **Issue:** Plan specified shadcn/ui Tabs but component not installed in project
- **Fix:** Created custom button group toggle with same visual appearance
- **Files modified:** web/src/features/matches/components/match-filters.tsx
- **Verification:** Build passes, toggle functions correctly
- **Committed in:** 302222e

---

**Total deviations:** 1 auto-fixed (blocking)
**Impact on plan:** Minimal - used existing components to achieve same functionality. No scope creep.

## Issues Encountered

None.

## Next Phase Readiness

- Phase 18-01 complete - Matches page now supports viewing competitor-only events
- Ready for Phase 19 (Palimpsest Comparison Page) if additional plans needed
- Events endpoint fully supports availability filtering for both pages

---
*Phase: 18-matches-page-filter*
*Completed: 2026-01-24*
