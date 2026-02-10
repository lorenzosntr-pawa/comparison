# UAT Issues: Phase 80 Plan 02

**Tested:** 2026-02-10
**Source:** .planning/phases/80-specifier-bug-fix/80-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all resolved]

## Resolved Issues

### UAT-001: Odds Comparison page mixes specifier lines for O/U 2.5 history

**Resolved:** 2026-02-10 - Fixed in 80-02-FIX.md
**Commit:** def055d
**Discovered:** 2026-02-10
**Phase/Plan:** 80-02
**Severity:** Major
**Feature:** Over/Under 2.5 inline market history on Odds Comparison page
**Description:** When clicking history for the Over/Under 2.5 inline market on the Odds Comparison page, the dialog shows mixed data from all O/U lines (1.5, 2.5, 3.5, etc.) instead of only 2.5 line data.
**Fix:** Changed `line: null` to `line: marketId === '5000' ? 2.5 : null` in match-table.tsx so O/U 2.5 history correctly filters to 2.5 line only. Other inline markets (1X2, BTTS, DC) still pass null as they don't have specifiers.

---

*Phase: 80-specifier-bug-fix*
*Plan: 02*
*Tested: 2026-02-10*
