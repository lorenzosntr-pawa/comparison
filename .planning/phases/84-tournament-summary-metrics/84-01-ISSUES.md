# UAT Issues: Phase 84 Plan 01

**Tested:** 2026-02-10
**Source:** .planning/phases/84-tournament-summary-metrics/84-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Tournaments API fails with page_size validation error

**Discovered:** 2026-02-10
**Phase/Plan:** 84-01
**Severity:** Blocker
**Feature:** Tournament list loading
**Description:** Historical Analysis page fails to load tournaments with 422 error. API rejects request because page_size=1000 exceeds maximum allowed value of 100.
**Expected:** Page loads and displays tournament list
**Actual:** "Failed to load tournaments: API error: 422" - validation error: "Input should be less than or equal to 100" for page_size parameter
**Repro:**
1. Navigate to /historical-analysis
2. Page attempts to load tournaments
3. API returns 422 with validation error

**Resolved:** 2026-02-10 - Fixed in 84-01-FIX.md
**Commit:** 95038da
**Fix:** Implemented pagination loop with page_size=100, fetching all pages until complete

---

*Phase: 84-tournament-summary-metrics*
*Plan: 01*
*Tested: 2026-02-10*
