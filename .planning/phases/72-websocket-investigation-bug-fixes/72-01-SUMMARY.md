---
phase: 72-websocket-investigation-bug-fixes
plan: 01
subsystem: ui
tags: [websocket, react, hooks, dashboard]

# Dependency graph
requires:
  - phase: 71-frontend-freshness
    provides: WebSocket infrastructure for real-time updates
provides:
  - Correct isObserving state that reflects actual scrape status
  - Dashboard idle state shows "Start New Scrape" button
affects: [dashboard, scrape-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Compound boolean for connection + activity state"

key-files:
  created: []
  modified:
    - web/src/features/dashboard/hooks/use-observe-scrape.ts

key-decisions:
  - "isObserving requires both activeScrapeId !== null AND ws.isConnected"

patterns-established:
  - "Compound state check: connection state alone insufficient for 'observing' status"

issues-created: []

# Metrics
duration: 3min
completed: 2026-02-09
---

# Phase 72 Plan 01: Fix "Always in Progress" Bug Summary

**Fixed isObserving logic to require active scrape ID, eliminating false progress display when WebSocket connects without active scrape**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-09T17:10:00Z
- **Completed:** 2026-02-09T17:13:00Z
- **Tasks:** 2 (1 auto + 1 checkpoint)
- **Files modified:** 1

## Accomplishments

- Fixed root cause: `isObserving` was returning `true` whenever WebSocket connected
- Changed condition from `ws.isConnected` to `activeScrapeId !== null && ws.isConnected`
- Dashboard now correctly shows "Start New Scrape" button when idle

## Task Commits

1. **Task 1: Fix isObserving logic** - `b9f635e` (fix)

**Plan metadata:** (this commit)

## Files Created/Modified

- `web/src/features/dashboard/hooks/use-observe-scrape.ts` - Fixed isObserving return value

## Decisions Made

- Used compound boolean check rather than separate flags - simpler and more explicit

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

- Bug fixed and verified working
- Ready for additional WebSocket reliability improvements in Phase 73

---
*Phase: 72-websocket-investigation-bug-fixes*
*Completed: 2026-02-09*
