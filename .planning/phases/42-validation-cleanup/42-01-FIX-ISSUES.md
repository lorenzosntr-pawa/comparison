# UAT Issues: Phase 42 Plan 01-FIX

**Tested:** 2026-01-29
**Source:** .planning/phases/42-validation-cleanup/42-01-FIX-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: BetPawa discovers competitions but fetches 0 events

**Discovered:** 2026-01-29
**Resolved:** 2026-01-29
**Resolution Commit:** `3bdf9d3`, `5ae53d4`
**Phase/Plan:** 42-01-FIX2
**Severity:** Blocker
**Feature:** BetPawa Event Discovery
**Description:** The API parsing fix successfully finds 155 BetPawa competitions, but the subsequent event fetching step returns 0 events. The competition-to-event conversion isn't working.

**Root Cause:** Two architectural mismatches:
1. Wrong response keys: code used `eventLists[].events[]` but API returns `responses[0].responses[]`
2. Missing full event fetch step: list response doesn't contain widgets array with SR ID

**Resolution:**
1. Fixed response parsing to use correct keys (`responses[0].responses`)
2. Added full event fetch step to get SR IDs from widgets array
3. Removed unused `_parse_betpawa_event` method (integrated logic into discovery)

---

*Phase: 42-validation-cleanup*
*Plan: 01-FIX*
*Tested: 2026-01-29*
