# UAT Issues: Phase 49 Plan 01

**Tested:** 2026-02-04
**Source:** .planning/phases/49-market-grouping/49-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-002: Markets should appear in multiple category tabs

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 49-01-FIX2.md
**Commit:** a56870d, 29839c7, 21cc782, 7322f69
**Phase/Plan:** 49-01
**Severity:** Major
**Feature:** Tabbed market navigation

**Description:** Markets with multiple tabs in BetPawa (e.g., a market that appears in both "Popular" and "Goals") only appear in one tab. The current implementation extracts only the first non-"all" tab, but markets should appear in every tab they belong to.

**Root Cause:** `event_coordinator.py` stored only a single `market_group` value instead of preserving the full tabs array.

**Fix Applied:** Changed `market_group` (string) to `market_groups` (JSON array). Now stores all non-"all" tabs and frontend filters by array membership.

### UAT-003: Some category tabs may still be missing

**Discovered:** 2026-02-04
**Resolved:** 2026-02-04 - Fixed in 49-01-FIX2.md
**Commit:** 7322f69
**Phase/Plan:** 49-01
**Severity:** Minor
**Feature:** Tabbed market navigation

**Description:** User reports seeing some tabs but expected more based on available markets. May indicate additional BetPawa categories not yet in TAB_ORDER.

**Fix Applied:** Unknown groups are now handled dynamically - they appear alphabetically before 'other' in the tab order, so no TAB_ORDER updates are needed for new categories.

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
