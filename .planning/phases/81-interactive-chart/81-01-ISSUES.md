# UAT Issues: Phase 81 Plan 01

**Tested:** 2026-02-10
**Source:** .planning/phases/81-interactive-chart/81-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: OddsLineChart click-to-lock doesn't persist

**Discovered:** 2026-02-10
**Resolved:** 2026-02-10
**Phase/Plan:** 81-01
**Severity:** Major
**Feature:** OddsLineChart Click-to-Lock
**Description:** Clicking on the odds line chart causes a brief visual flash but doesn't lock the chart. No vertical reference line appears and the tooltip continues to follow the mouse.
**Root Cause:** Time string comparison for toggle could fail due to format differences; stale closure in useCallback; no debounce for rapid clicks.
**Fix:** Used index-based comparison with refs, added 100ms debounce, explicit bounds checking.
**Fix Commit:** `42959da`

### UAT-002: MarginLineChart click-to-lock doesn't persist

**Discovered:** 2026-02-10
**Resolved:** 2026-02-10
**Phase/Plan:** 81-01
**Severity:** Major
**Feature:** MarginLineChart Click-to-Lock
**Description:** Same issue as OddsLineChart - clicking causes brief flash but no persistent lock.
**Root Cause:** Same as UAT-001.
**Fix:** Same fixes applied to MarginLineChart.
**Fix Commit:** `42959da`

### UAT-003: Comparison panel doesn't appear

**Discovered:** 2026-02-10
**Resolved:** 2026-02-10
**Phase/Plan:** 81-01
**Severity:** Major
**Feature:** Locked Comparison Panel
**Description:** No comparison panel appears below the charts after clicking. The panel should show all bookmaker values at the locked timestamp.
**Root Cause:** Panel visibility depended on `isLocked` and `lockedIndex` which weren't persisting due to the click handler issues.
**Fix:** Fixed underlying click handler; panel now renders correctly when locked.
**Fix Commit:** `42959da`

---

*Phase: 81-interactive-chart*
*Plan: 01*
*Tested: 2026-02-10*
*All issues resolved: 2026-02-10*
