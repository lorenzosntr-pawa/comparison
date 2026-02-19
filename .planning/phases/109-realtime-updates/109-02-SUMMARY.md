---
phase: 109-realtime-updates
plan: 02
subsystem: ui
tags: [websocket, tanstack-query, sidebar, badge, real-time]

# Dependency graph
requires:
  - phase: 109-01
    provides: WebSocket alert broadcasting, risk_alerts topic
provides:
  - Real-time alert UI updates via WebSocket
  - Sidebar alert badge for visibility
affects: [risk-monitoring]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - useRiskAlertUpdates follows useOddsUpdates pattern for consistency

key-files:
  created:
    - web/src/features/risk-monitoring/hooks/use-risk-alert-updates.ts
  modified:
    - web/src/features/risk-monitoring/hooks/index.ts
    - web/src/App.tsx
    - web/src/components/layout/app-sidebar.tsx

key-decisions:
  - "Global subscription in App.tsx for automatic query invalidation"
  - "Badge shows only NEW alerts count from byStatus.new"
  - "Red badge with 99+ cap for high visibility"

patterns-established:
  - "Real-time feature update hook pattern: subscribe to topic, invalidate queries on message"
  - "Sidebar badge pattern: useStats hook + conditional badge rendering"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-19
---

# Phase 109 Plan 02: Frontend Real-Time Updates Summary

**Real-time alert subscription via WebSocket and sidebar badge showing new alert count**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-19T15:30:00Z
- **Completed:** 2026-02-19T15:38:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint)
- **Files modified:** 4

## Accomplishments

- Created useRiskAlertUpdates hook subscribing to risk_alerts WebSocket topic
- Added global subscription in App.tsx for automatic query invalidation
- Added Risk Monitoring link to sidebar navigation with AlertTriangle icon
- Implemented red badge showing new alert count (capped at 99+)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create useRiskAlertUpdates hook** - `ec1dd6a` (feat)
2. **Task 2: Add Risk Monitoring link with badge to sidebar** - `40d3cb6` (feat)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified

- `web/src/features/risk-monitoring/hooks/use-risk-alert-updates.ts` - WebSocket subscription hook
- `web/src/features/risk-monitoring/hooks/index.ts` - Added export
- `web/src/App.tsx` - Global hook subscription
- `web/src/components/layout/app-sidebar.tsx` - Navigation link and badge

## Decisions Made

- Global subscription in App.tsx ensures all pages benefit from real-time updates
- Badge shows only NEW (unacknowledged) alerts using byStatus.new from stats
- Red badge (bg-red-500) for high visibility, capped at 99+ for large counts

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Phase 109 complete, all 2 plans finished
- Ready for Phase 110: Cross-Page Integration

---
*Phase: 109-realtime-updates*
*Completed: 2026-02-19*
