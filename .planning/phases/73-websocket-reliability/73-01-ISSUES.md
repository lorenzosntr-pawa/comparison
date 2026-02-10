# UAT Issues: Phase 73 Plan 01

**Tested:** 2026-02-09
**Source:** .planning/phases/73-websocket-reliability/73-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-002: React key warning - duplicate keys '0-1'

**Discovered:** 2026-02-09
**Phase/Plan:** 73-01 (observed during testing, likely pre-existing)
**Severity:** Cosmetic
**Feature:** Dashboard/odds table rendering
**Description:** Console warning: "Encountered two children with the same key, `0-1`. Keys should be unique so that components maintain their identity across updates." Warning appears multiple times during initial page load.
**Expected:** No React key warnings in console
**Actual:** Warning appears 8+ times, though no visible UI issues
**Repro:**
1. Open browser dev tools console
2. Navigate to dashboard
3. Observe console warnings about duplicate keys

**Note:** This is likely a pre-existing issue not introduced by Phase 73. Recommend addressing during Phase 75 (Dead Code Audit - Frontend) as part of code quality improvements.

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
