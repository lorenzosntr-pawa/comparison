# UAT Issues: Phase 42 Plan 01-FIX3

**Tested:** 2026-02-02
**Source:** .planning/phases/42-validation-cleanup/42-01-FIX3-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: No odds snapshots created during scraping

**Discovered:** 2026-02-02
**Phase/Plan:** 42-01-FIX3
**Severity:** Blocker
**Feature:** Odds data capture
**Description:** Scraping runs complete event discovery successfully (BetPawa 919, SportyBet 993, Bet9ja 939) but creates zero odds snapshots. Logs show `snapshots_created=0` for every batch while `events_stored=50` succeeds.
**Expected:** Each batch should create odds snapshots for the events being stored. Odds Comparison page should show odds data for all platforms.
**Actual:** `snapshots_created=0` in every batch. Odds Comparison page shows no odds data for any platform.
**Repro:**
1. Start the application
2. Trigger a scrape run
3. Observe logs showing `snapshots_created=0` repeatedly
4. Navigate to Odds Comparison page - no odds data displayed

**Log evidence:**
```
2026-02-02T09:03:31.514399Z [info] Batch storage complete batch_id=batch_41768569 errors=0 events_stored=50 snapshots_created=0
2026-02-02T09:03:47.373284Z [info] Batch storage complete batch_id=batch_9260323b errors=0 events_stored=50 snapshots_created=0
...
```

## Resolved Issues

[None yet]

---

*Phase: 42-validation-cleanup*
*Plan: 01-FIX3*
*Tested: 2026-02-02*
