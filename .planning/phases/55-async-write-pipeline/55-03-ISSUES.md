# UAT Issues: Phase 55 Plan 03

**Tested:** 2026-02-05
**Source:** .planning/phases/55-async-write-pipeline/55-03-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: Write handler fails with timezone mismatch on last_confirmed_at

**Discovered:** 2026-02-05
**Phase/Plan:** 55-03
**Severity:** Blocker
**Feature:** Async write queue persistence
**Description:** Every write batch fails with `asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes`. The `last_confirmed_at` column is `TIMESTAMP WITHOUT TIME ZONE` in the DB schema, but the write handler passes `datetime.datetime(..., tzinfo=datetime.timezone.utc)` (timezone-aware). asyncpg rejects the type mismatch. All batches exhaust 3 retry attempts and are dropped.
**Expected:** Write handler should persist changed snapshots to the database without errors.
**Actual:** All write batches fail after 3 retries. Changed competitor snapshots are never persisted. Data is served from cache but lost on restart.
**Repro:**
1. Start the application
2. Let a scheduled scrape cycle run (uses async write queue path)
3. Observe `write_batch_failed` and `write_batch_retry` errors in terminal logs
4. Error: `can't subtract offset-naive and offset-aware datetimes`

### UAT-002: On-demand scrape perceived as slower

**Discovered:** 2026-02-05
**Phase/Plan:** 55-03
**Severity:** Minor
**Feature:** On-demand scrape (button trigger)
**Description:** User reports on-demand scrape feels slower than before Phase 55. On-demand uses the sync fallback path (no write queue), but Phase 55 refactored store_batch_results which may have added overhead in the common code path (storage lookups, reconciliation, EventBookmaker creation).
**Expected:** On-demand scrape performance should be unchanged from pre-Phase 55.
**Actual:** User perceives scrape is slower. Batch timing shows ~35-47s per 50-event batch. No baseline comparison available from this session.
**Repro:**
1. Start the application
2. Click the scrape button to trigger an on-demand scrape
3. Observe batch timing in logs

## Resolved Issues

[None yet]

---

*Phase: 55-async-write-pipeline*
*Plan: 03*
*Tested: 2026-02-05*
