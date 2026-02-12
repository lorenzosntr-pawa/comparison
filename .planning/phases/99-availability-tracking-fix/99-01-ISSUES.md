# UAT Issues: Phase 99 Plan 01

**Tested:** 2026-02-12
**Source:** .planning/phases/99-availability-tracking-fix/99-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: UnboundLocalError on `update` variable

**Discovered:** 2026-02-12
**Phase/Plan:** 99-01
**Severity:** Blocker
**Feature:** Availability persistence
**Description:** Scrape crashes at line 1291 with `UnboundLocalError: cannot access local variable 'update'`
**Expected:** Scrape completes and persists availability data
**Actual:** Scrape fails immediately on first batch
**Root cause:** Local import at line 1688 (`from sqlalchemy import update`) shadows module-level import
**Repro:**
1. Start backend
2. Trigger manual scrape
3. Observe crash on first batch storage

### UAT-002: Stale odds not marked as unavailable

**Discovered:** 2026-02-12
**Phase/Plan:** 99-01 (but root cause pre-dates Phase 99)
**Severity:** Major
**Feature:** Availability detection
**Description:** Event 4304 shows Bet9ja odds from 5+ hours ago as "available" despite not being scraped recently
**Expected:** Markets should be marked unavailable if the event wasn't in recent scrapes
**Actual:** Old data persists with `available: true`, no staleness indication
**Root cause:** Availability detection only runs for events that ARE scraped. Events NOT scraped (not in discovery or scrape failed) are never checked.
**Repro:**
1. Wait for a scrape cycle where SportyBet times out
2. Find an event with stale competitor data (e.g., event 4304, Bet9ja snapshot from 09:53)
3. Note that old odds show as "available" despite being hours old

## Resolved Issues

### UAT-001: UnboundLocalError on `update` variable
**Resolved:** 2026-02-12 - Removed redundant local imports at lines 1688-1690
**Fix:** Deleted `from sqlalchemy import update` and related imports that shadowed module-level imports

---

*Phase: 99-availability-tracking-fix*
*Plan: 01*
*Tested: 2026-02-12*
