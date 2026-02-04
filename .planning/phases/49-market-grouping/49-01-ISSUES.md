# UAT Issues: Phase 49 Plan 01

**Tested:** 2026-02-04
**Source:** .planning/phases/49-market-grouping/49-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Missing market category tabs (Combos, Specials, Popular)

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 49-01-FIX.md
**Commit:** 871a9b8
**Phase/Plan:** 49-01
**Severity:** Blocker
**Feature:** Tabbed market navigation

**Description:** Only a subset of market category tabs were shown. BetPawa data contained market groups that didn't appear as tabs.

**Root Cause:** TAB_ORDER in market-grid.tsx only included `['all', 'main', 'goals', 'handicaps', 'halves', 'corners', 'cards', 'other']` but BetPawa uses `popular` (not `main`) and also has `combos` and `specials` categories.

**Fix Applied:** Updated TAB_ORDER to `['all', 'popular', 'goals', 'handicaps', 'combos', 'halves', 'corners', 'cards', 'specials', 'other']` and added corresponding TAB_NAMES entries.

---

*Phase: 49-market-grouping*
*Plan: 01*
*Tested: 2026-02-04*
