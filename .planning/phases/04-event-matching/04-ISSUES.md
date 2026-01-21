# UAT Issues: Phase 4

**Tested:** 2026-01-20
**Source:** .planning/phases/04-event-matching/04-01-SUMMARY.md, 04-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-001: Scraper orchestrator returns empty arrays (BLOCKER)

**Discovered:** 2026-01-20
**Phase/Plan:** 04 (blocked by Phase 3 stub code)
**Severity:** Blocker
**Feature:** Event list endpoint (GET /events/)
**Description:** Phase 4 cannot be tested because the scraper orchestrator's `_scrape_platform` method returns empty arrays for all platforms. The code at [orchestrator.py:164-185](src/scraping/orchestrator.py#L164-L185) contains placeholder stubs with comments like "Return empty list for now - actual event fetching will be enhanced".
**Expected:** Scrape populates database with real events from Betpawa/SportyBet/Bet9ja
**Actual:** Scrape succeeds but returns 0 events - orchestrator never fetches actual event data

**Analysis:**
This is not a Phase 4 bug - Phase 3 created the scraper infrastructure but left event fetching as stubs. The scraper clients can check health, but the orchestrator doesn't call the actual event fetching methods.

**Repro:**
1. Start server: `python -m uvicorn src.api.app:create_app --factory`
2. Call: `POST http://localhost:8000/scrape`
3. Response shows `total_events: 0` with `success: true` for platforms

## Resolved Issues

### UAT-002: ScrapeStatus enum mismatch (FIXED)

**Discovered:** 2026-01-20
**Resolved:** 2026-01-20
**Severity:** Major
**Description:** [jobs.py:68](src/scheduling/jobs.py#L68) called `ScrapeStatus(result.status.upper())` but StrEnum values are lowercase.
**Fix:** Removed `.upper()` call since orchestrator returns lowercase status strings.

### UAT-003: Timezone-aware datetime mismatch (FIXED)

**Discovered:** 2026-01-20
**Resolved:** 2026-01-20
**Severity:** Major
**Description:** Code passed `datetime.now(timezone.utc)` to `completed_at` column, but database column is `TIMESTAMP WITHOUT TIME ZONE`.
**Fix:** Changed to `datetime.utcnow()` in jobs.py:70, jobs.py:88, and scrape.py:82.

---

*Phase: 04-event-matching*
*Tested: 2026-01-20*
