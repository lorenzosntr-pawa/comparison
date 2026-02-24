# UAT Issues: Phase 110 Plan 01

**Tested:** 2026-02-24
**Source:** .planning/phases/110-retention-cleanup-storage-fix/110-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: Cleanup execute fails with FK violation on scrape_runs

**Discovered:** 2026-02-24
**Phase/Plan:** 110-01
**Severity:** Blocker
**Feature:** Cleanup execute endpoint
**Description:** When executing cleanup, the process proceeds through all tables correctly (market_odds, odds_snapshots, competitor_market_odds, competitor_odds_snapshots, market_odds_history, scrape_errors, scrape_phase_logs) but then crashes when trying to delete old scrape_runs with a ForeignKeyViolationError.
**Expected:** Cleanup should complete successfully, deleting all old records including scrape_runs
**Actual:** 500 Internal Server Error with `asyncpg.exceptions.ForeignKeyViolationError: update or delete on table "scrape_runs"`
**Repro:**
1. Navigate to Settings page
2. Preview cleanup shows records to delete
3. Click Execute cleanup button
4. Error 500 occurs

**Root Cause (confirmed):** The `event_scrape_status` table has a FK to `scrape_runs.id` (line 42 of event_scrape_status.py):
```python
scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_runs.id"))
```
But `cleanup.py` does NOT delete `event_scrape_status` records before attempting to delete `scrape_runs`. The table was added in v1.7 but was never added to the cleanup procedure.

**Fix:** Add `EventScrapeStatus` deletion between scrape_phase_logs (step 7) and scrape_runs (step 8) in cleanup.py.

**Files to modify:**
- `src/services/cleanup.py` - Add EventScrapeStatus import and deletion step
- `src/api/schemas/cleanup.py` - Add event_scrape_status_count to preview/result schemas (optional)

**Technical details from error:**
```
ForeignKeyViolationError: update or delete on table "scrape_runs"
[SQL: DELETE FROM scrape_runs WHERE scrape_runs.started_at < ...]
```

## Resolved Issues

[None yet]

---

*Phase: 110-retention-cleanup-storage-fix*
*Plan: 01*
*Tested: 2026-02-24*
