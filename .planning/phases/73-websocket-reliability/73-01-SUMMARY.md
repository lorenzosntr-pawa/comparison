---
phase: 73-websocket-reliability
plan: 01
subsystem: ui
tags: [websocket, react, tanstack-query, reconnection]

# Dependency graph
requires:
  - phase: 72
    provides: Fixed isObserving compound boolean requiring active scrape
provides:
  - onReconnect callback for WebSocket hooks
  - Manual reconnect function for error recovery
  - ConnectionStatusIndicator component
  - Query invalidation on reconnection
affects: [74-dead-code-audit-backend, real-time-updates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - wasConnectedRef pattern for detecting reconnection vs initial connect
    - Stable connection timeout (30s) before retry counter reset

key-files:
  created:
    - web/src/components/ui/connection-status.tsx
  modified:
    - web/src/hooks/use-websocket.ts
    - web/src/hooks/use-websocket-scrape-progress.ts
    - web/src/hooks/use-odds-updates.ts
    - web/src/features/dashboard/hooks/use-observe-scrape.ts
    - web/src/features/dashboard/components/status-bar.tsx

key-decisions:
  - "Reset retry counter after 30s stable connection (not immediately)"
  - "Fire onReconnect only on disconnected→connected transition (not initial connect)"
  - "Integrate WebSocket indicator into existing StatusBar component"

patterns-established:
  - "wasConnectedRef pattern: track first connection to distinguish reconnection from initial connect"
  - "stableConnectionTimeout pattern: delay retry counter reset to avoid premature reset on flaky connections"

issues-created: []

# Metrics
duration: 8min
completed: 2026-02-09
---

# Phase 73 Plan 01: WebSocket Reliability Summary

**Added reconnect callbacks with query invalidation, connection status indicator with manual retry button in dashboard**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-09T15:30:00Z
- **Completed:** 2026-02-09T15:38:00Z
- **Tasks:** 2
- **Files modified:** 6 (1 created, 5 modified)

## Accomplishments
- Added `onReconnect` callback option to useWebSocket hook that fires on reconnection (not initial connect)
- Added `reconnect()` function for manual reconnection with retry state reset
- Reset retry counter after 30 seconds of stable connection (prevents immediate reset on flaky networks)
- Created ConnectionStatusIndicator component with visual states (green/yellow/gray/red)
- Integrated WebSocket status into dashboard StatusBar with Retry button in error state
- Query invalidation on reconnect ensures UI stays fresh after network recovery

## Task Commits

Each task was committed atomically:

1. **Task 1: Add reconnect callbacks and query invalidation** - `640eecf` (feat)
2. **Task 2: Add connection status indicator with manual reconnect** - `7518af4` (feat)

**Plan metadata:** (pending this commit)

## Files Created/Modified
- `web/src/components/ui/connection-status.tsx` - New ConnectionStatusIndicator component
- `web/src/hooks/use-websocket.ts` - Added onReconnect callback, reconnect function, wasConnectedRef
- `web/src/hooks/use-websocket-scrape-progress.ts` - Added handleReconnect, exposed connectionState
- `web/src/hooks/use-odds-updates.ts` - Added handleReconnect callback
- `web/src/features/dashboard/hooks/use-observe-scrape.ts` - Exposed connectionState and reconnect
- `web/src/features/dashboard/components/status-bar.tsx` - Integrated WebSocket status indicator

## Decisions Made
- Fire onReconnect only on reconnection (not initial connect) using wasConnectedRef pattern
- Reset retry counter after 30s stable connection to prevent premature reset
- Use existing StatusBar component for WebSocket indicator (consistent with DB/Scheduler indicators)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness
- WebSocket connection lifecycle improved
- Users can see connection status and manually retry
- Data stays fresh after reconnection events
- Ready for Phase 74: Dead Code Audit & Removal (Backend)

---
*Phase: 73-websocket-reliability*
*Completed: 2026-02-09*
