---
phase: 110-cross-page-integration
plan: 01
subsystem: ui
tags: [react, tanstack-query, websocket, alerts, navigation]

# Dependency graph
requires:
  - phase: 109
    provides: WebSocket alert broadcasting, Risk Monitoring page
  - phase: 108
    provides: Event grouping with max severity
provides:
  - Event-specific alert hooks (useEventAlerts, useEventAlertSummary, useEventAlertCounts)
  - AlertIndicator component for severity-colored badges
  - Alert banner on Event Details page
  - Alert badges on Odds Comparison table rows
  - Navigation links to Risk Monitoring with event_id filter
affects: [111-settings]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Batch alert fetching with useQueries for visible events"
    - "Severity-based color theming (warning/elevated/critical)"
    - "Cross-page navigation with query params"

key-files:
  created:
    - web/src/features/matches/hooks/use-event-alerts.ts
    - web/src/features/matches/components/alert-indicator.tsx
  modified:
    - web/src/features/matches/hooks/index.ts
    - web/src/features/matches/components/index.ts
    - web/src/features/matches/components/match-header.tsx
    - web/src/features/matches/components/match-table.tsx
    - web/src/features/matches/index.tsx

key-decisions:
  - "Batch fetch alerts using useQueries for all visible events to minimize API calls"
  - "Only fetch alerts for positive event IDs (competitor-only events have negative IDs)"
  - "AlertIndicator uses stopPropagation to prevent row click when clicking badge"

patterns-established:
  - "useEventAlertCounts pattern for batch fetching entity-specific data"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-19
---

# Phase 110 Plan 01: Cross-Page Integration Summary

**Alert indicators on Odds Comparison and Event Details pages with click-to-navigate to Risk Monitoring filtered by event**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-19T14:30:00Z
- **Completed:** 2026-02-19T14:38:00Z
- **Tasks:** 4 (+ 1 verification checkpoint)
- **Files modified:** 7

## Accomplishments

- Created useEventAlerts hooks for fetching alerts for specific events
- Built AlertIndicator component with severity-colored badges (yellow/orange/red)
- Added alert banner to Event Details page header with "View Alerts" navigation
- Added alert badges to Odds Comparison table next to event names
- All navigation links filter Risk Monitoring by event_id query param

## Task Commits

Each task was committed atomically:

1. **Task 1: Create useEventAlerts hook** - `55e1d5a` (feat)
2. **Task 2: Create AlertIndicator component** - `8306386` (feat)
3. **Task 3: Integrate alerts into MatchDetail header** - `354b5fe` (feat)
4. **Task 4: Integrate alerts into MatchTable rows** - `55b6676` (feat)

## Files Created/Modified

- `web/src/features/matches/hooks/use-event-alerts.ts` - New hooks for event-specific alerts
- `web/src/features/matches/components/alert-indicator.tsx` - Severity-colored badge component
- `web/src/features/matches/hooks/index.ts` - Export new hooks
- `web/src/features/matches/components/index.ts` - Export AlertIndicator
- `web/src/features/matches/components/match-header.tsx` - Alert banner in event header
- `web/src/features/matches/components/match-table.tsx` - Alert badges on table rows
- `web/src/features/matches/index.tsx` - Wire up useEventAlertSummary in MatchDetail

## Decisions Made

- **Batch fetching with useQueries:** Fetch alerts for all visible events in parallel to minimize API round-trips
- **Positive IDs only:** Only fetch alerts for events with positive IDs since competitor-only events (negative IDs) can't have alerts
- **stopPropagation on badge click:** Prevent row navigation when clicking the alert badge to navigate to Risk Monitoring

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Cross-page alert visibility complete
- Ready for Phase 111: Settings & Configuration
- Alert thresholds and retention settings to be configurable via UI

---
*Phase: 110-cross-page-integration*
*Completed: 2026-02-19*
