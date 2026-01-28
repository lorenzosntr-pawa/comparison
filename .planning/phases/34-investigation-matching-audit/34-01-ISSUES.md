# UAT Issues: Phase 34 Plan 01

**Tested:** 2026-01-28
**Source:** .planning/phases/34-investigation-matching-audit/34-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - moved to Resolved]

## Resolved Issues

### UAT-001: Frontend displays incorrect/stale data despite healthy backend

**Discovered:** 2026-01-28
**Resolved:** 2026-01-28 (Phase 34.1 audit)
**Phase/Plan:** 34-01
**Severity:** Major
**Feature:** Data display across application
**Description:** User reports that while the backend matching audit confirms 99.9% accuracy, the frontend displays:
- Odds not correctly updated / stale values
- Too many matches showing as "unmatched"
- Overall poor data quality in UI

This affects multiple pages across the application (Odds Comparison, Matches, Dashboard widgets).

**Root Cause Identified (Phase 34.1):**
Two API-layer bugs were found:

1. **API-001 (Critical):** `/palimpsest/coverage` counts raw competitor rows instead of unique events (inflates competitor_only_count by 92%)
   - Location: `src/api/routes/palimpsest.py:119-127`
   - Fix: Use `func.count(distinct(CompetitorEvent.sportradar_id))` instead of `func.count()`

2. **API-002 (Major):** Event detail endpoint uses legacy odds system with limited competitor data
   - Location: `src/api/routes/events.py:640-667`
   - Fix: Also query `competitor_events` + `competitor_odds_snapshots` tables

**Resolution:**
Root causes fully documented in `.planning/phases/34.1-api-ui-data-flow-audit/AUDIT-FINDINGS.md`. Fixes to be implemented in Phase 35.

---

*Phase: 34-investigation-matching-audit*
*Plan: 01*
*Tested: 2026-01-28*
