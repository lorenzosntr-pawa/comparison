# UAT Issues: Phase 42 Plan 01-FIX2

**Tested:** 2026-01-29
**Source:** .planning/phases/42-validation-cleanup/42-01-FIX2-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: BetPawa event discovery still returns 0 events

**Discovered:** 2026-01-29
**Phase/Plan:** 42-01-FIX2
**Severity:** Blocker
**Feature:** BetPawa Event Discovery
**Description:** Despite the fix in 42-01-FIX2, BetPawa discovery still returns 0 events. The log shows 159 competitions found, but 0 events extracted.
**Expected:** BetPawa should discover events (similar to SportyBet 1219 and Bet9ja 1162)
**Actual:** "Discovered BetPawa events count=0" while other platforms work fine

**Resolution:** 2026-01-29 (Commit: e29e1e8)
**Root cause:** SR ID extraction path was wrong. Code was using `widget.get("data", {}).get("matchId")` but the old working code used `widget.get("id")` directly. The SPORTRADAR widget stores the SR ID in its `id` field, not in `data.matchId`.
**Fix:** Changed SR ID extraction to use `widget.get("id")` first, falling back to `widget.data.matchId`. Also optimized to extract SR IDs from list response before doing full event fetches.
**Verified:** BetPawa now discovers 1021 events (similar to SportyBet 1218 and Bet9ja 1165)

---

*Phase: 42-validation-cleanup*
*Plan: 01-FIX2*
*Tested: 2026-01-29*
