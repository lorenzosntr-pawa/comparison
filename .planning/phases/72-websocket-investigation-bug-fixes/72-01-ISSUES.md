# UAT Issues: Phase 72 Plan 1

**Tested:** 2026-02-09
**Source:** .planning/phases/72-websocket-investigation-bug-fixes/72-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: WebSocket console noise during React StrictMode double-invoke

**Discovered:** 2026-02-09
**Phase/Plan:** 72-01
**Severity:** Cosmetic
**Feature:** WebSocket connection
**Description:** During app startup in development mode, React StrictMode double-invokes effects, causing WebSocket connections to be opened and closed rapidly. This produces console warnings like "WebSocket is closed before the connection is established" before the reconnection logic recovers.
**Expected:** Clean console output without transient connection warnings
**Actual:** Multiple WebSocket warning lines during initial mount, then successful reconnection after 1 retry
**Repro:**
1. Open app in development mode (npm run dev)
2. Open browser DevTools console
3. Refresh the page
4. Observe WebSocket connection warnings before successful connection

**Note:** This is expected React 18+ StrictMode behavior, not a bug. Recommend addressing in Phase 73 (WebSocket Reliability) by either:
- Using a connection delay/debounce
- Suppressing the warning during cleanup
- Checking component mount state before connecting

## Resolved Issues

[None yet]

---

*Phase: 72-websocket-investigation-bug-fixes*
*Plan: 01*
*Tested: 2026-02-09*
