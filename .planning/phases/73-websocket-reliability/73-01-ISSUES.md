# UAT Issues: Phase 73 Plan 01

**Tested:** 2026-02-09
**Source:** .planning/phases/73-websocket-reliability/73-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Retry button not appearing in disconnected state

**Discovered:** 2026-02-09
**Phase/Plan:** 73-01
**Severity:** Minor
**Feature:** Connection status indicator with manual reconnect
**Description:** When backend is stopped and WebSocket fails to connect, the indicator turns gray (disconnected) but no "Retry" button appears. Even after waiting for multiple retry attempts to exhaust, the Retry button never shows.
**Expected:** Retry button should appear in error/disconnected state per PLAN.md specification
**Actual:** Indicator turns gray, stays gray, no Retry button visible
**Repro:**
1. Stop the backend server
2. Refresh the browser
3. Wait for WebSocket retry attempts
4. Observe: indicator turns gray, no Retry button

**Resolved:** 2026-02-09 - Fixed in 73-01-FIX.md
**Commit:** 3900f65
**Fix:** Changed Retry button condition from `state === 'error'` to `(state === 'error' || state === 'disconnected')`

---

*Phase: 73-websocket-reliability*
*Plan: 01*
*Tested: 2026-02-09*
