# UAT Issues: Phase 66 Plan 01

**Tested:** 2026-02-08
**Source:** .planning/phases/66-odds-comparison-history/66-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all resolved]

## Resolved Issues

### UAT-001: Page crashes to blank when clicking odds cell

**Discovered:** 2026-02-08
**Resolved:** 2026-02-08
**Phase/Plan:** 66-01
**Severity:** Blocker
**Feature:** Odds cell click opens history dialog
**Description:** When clicking on an odds value cell, the entire page goes blank. Nothing is shown - requires page refresh to see content again.
**Expected:** History dialog opens showing odds history chart
**Actual:** Page crashes to blank, requires refresh
**Repro:**
1. Navigate to Odds Comparison page
2. Click on any odds value cell (e.g., 1X2 odds for any bookmaker)
3. Page goes completely blank
**Resolution:** Missing React keys on Fragment elements in `visibleMarkets.map()` caused React reconciliation to fail. Fixed by changing `<>...</>` to `<Fragment key={marketId}>...</Fragment>` in match-table.tsx.

### UAT-002: Page crashes to blank when clicking margin cell

**Discovered:** 2026-02-08
**Resolved:** 2026-02-08
**Phase/Plan:** 66-01
**Severity:** Blocker
**Feature:** Margin cell click opens history dialog
**Description:** When clicking on a margin percentage cell, the entire page goes blank. Same behavior as odds cell click.
**Expected:** History dialog opens showing margin history chart
**Actual:** Page crashes to blank, requires refresh
**Repro:**
1. Navigate to Odds Comparison page
2. Click on any margin percentage cell
3. Page goes completely blank
**Resolution:** Same root cause as UAT-001. Fixed with Fragment key addition.

---

*Phase: 66-odds-comparison-history*
*Plan: 01*
*Tested: 2026-02-08*
