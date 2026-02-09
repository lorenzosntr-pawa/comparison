# UAT Issues: Phase 71 Plan 01

**Tested:** 2026-02-09
**Source:** .planning/phases/71-frontend-freshness-fixes/71-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all resolved]

## Resolved Issues

### UAT-001: WebSocket connection fails - Vite proxy not forwarding WS

**Discovered:** 2026-02-09
**Phase/Plan:** 71-01
**Severity:** Blocker
**Feature:** WebSocket odds_updates subscription
**Description:** WebSocket connection to `ws://localhost:5173/api/ws?topics=odds_updates` failed with code 1006. The Vite dev server proxy was not forwarding WebSocket connections to the backend.
**Expected:** WebSocket connects successfully and receives odds_update messages from backend
**Actual:** "WebSocket is closed before the connection is established" - connection failed immediately
**Root Cause:** Vite proxy configuration missing `ws: true` for WebSocket forwarding
**Resolved:** 2026-02-09 - Added `ws: true` to vite.config.ts proxy configuration

### UAT-002: Timestamps show stale time despite odds being correct

**Discovered:** 2026-02-09
**Phase/Plan:** 71-01
**Severity:** Major
**Feature:** Fresh timestamp display
**Description:** Timestamps on Odds Comparison page showed "1h ago" or older, even though scrapes had run recently and odds values appeared correct.
**Expected:** Timestamps show recent time (within ~2 minutes of last scrape)
**Actual:** Timestamps showed 1+ hours ago
**Root Cause:** API sends UTC timestamps without 'Z' suffix, and JavaScript's `new Date()` interpreted them as local time instead of UTC, causing a timezone offset
**Resolved:** 2026-02-09 - Added UTC normalization to `formatRelativeTime()` in market-utils.ts and manage-data-button.tsx

### UAT-003: No real-time timestamp updates after scrape

**Discovered:** 2026-02-09
**Phase/Plan:** 71-01
**Severity:** Major
**Feature:** Real-time query invalidation
**Description:** After a scrape completed, timestamps did not update automatically.
**Expected:** Timestamps update automatically when scrape completes (WebSocket → query invalidation)
**Actual:** Nothing changed at all after scrape
**Root Cause:** Blocked by UAT-001 (WebSocket not connecting)
**Resolved:** 2026-02-09 - Fixed by resolving UAT-001 (WebSocket now connects and delivers odds_update messages)

---

*Phase: 71-frontend-freshness-fixes*
*Plan: 01*
*Tested: 2026-02-09*
*All issues resolved: 2026-02-09*
