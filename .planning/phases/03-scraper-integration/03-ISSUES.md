# UAT Issues: Phase 3 - Scraper Integration

**Tested:** 2026-01-21
**Source:** .planning/phases/03-scraper-integration/03-*-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: GET /scrape/{id} crashes with AttributeError

**Discovered:** 2026-01-21
**Phase/Plan:** 03-06
**Severity:** Major
**Feature:** Scrape run status query endpoint
**Description:** GET /scrape/{id} endpoint crashes with `AttributeError: 'str' object has no attribute 'value'` when trying to retrieve a scrape run's status.
**Expected:** Returns JSON response with scrape run details including status, timestamps, and platform results.
**Actual:** Server returns 500 Internal Server Error. The error occurs at `src/api/routes/scrape.py:127` where `scrape_run.status.value` is called, but `status` is already a string, not an enum.
**Repro:**
1. POST /scrape to create a scrape run (note the scrape_run_id)
2. GET /scrape/{id} using that ID
3. Observe 500 error

**Resolved:** 2026-01-21 - Fixed in 03-FIX.md
**Fix:** Removed `.value` from `scrape_run.status.value` since SQLAlchemy returns status as string, not enum

---

*Phase: 03-scraper-integration*
*Tested: 2026-01-21*
