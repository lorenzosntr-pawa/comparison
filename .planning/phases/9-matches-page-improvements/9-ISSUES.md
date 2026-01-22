# UAT Issues: Phase 10

**Tested:** 2026-01-21
**Source:** .planning/phases/10-matches-page-improvements/10-01-SUMMARY.md, 10-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-002: League names not distinguishable without region

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21 — Fixed during UAT session
**Phase/Plan:** 10-02
**Severity:** Minor
**Feature:** Searchable multi-select league filter
**Description:** Leagues with the same name in different countries could not be distinguished in the dropdown. Also, only tournaments from the current page of events were shown.
**Fix:**
1. Added country display next to league name in dropdown
2. Created dedicated `/events/tournaments` API endpoint to fetch all tournaments
3. Updated frontend to use new endpoint instead of extracting from events

### UAT-001: Date filter causes API 500 error

**Discovered:** 2026-01-21
**Resolved:** 2026-01-21 — Fixed during UAT session
**Phase/Plan:** 10-02
**Severity:** Blocker
**Feature:** Date filter presets and manual date input
**Root cause:** Browser sends timezone-aware datetime (ISO 8601 with Z suffix), but database stores naive UTC. The query tried to compare timezone-aware filter params with naive `now` datetime.
**Fix:** Strip timezone info from filter dates in `src/api/routes/events.py` lines 523-530

---

*Phase: 10-matches-page-improvements*
*Tested: 2026-01-21*
