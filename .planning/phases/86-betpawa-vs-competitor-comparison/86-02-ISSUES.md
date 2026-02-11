# UAT Issues: Phase 86 Plan 02

**Tested:** 2026-02-11
**Source:** .planning/phases/86-betpawa-vs-competitor-comparison/86-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: MarketCard column alignment issues

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11 - Fixed in 86-02-FIX.md
**Commit:** dfc0e62
**Phase/Plan:** 86-02
**Severity:** Major
**Feature:** Multi-column MarketCard layout
**Description:** Columns in the multi-bookmaker comparison table are not well aligned
**Fix:** Used consistent gridStyle with 5.5rem label column and minmax for bookmaker columns

### UAT-002: Missing opening/closing margins for competitors

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11 - Fixed in 86-02-FIX.md
**Commit:** dfc0e62
**Phase/Plan:** 86-02
**Severity:** Major
**Feature:** Multi-column MarketCard layout
**Description:** Opening/closing margin data is only shown for Betpawa, not for competitor bookmakers
**Fix:** Extended MarketMarginStats with openingMargin/closingMargin, added Opening/Closing rows to table

### UAT-003: CompetitiveBadge not visible enough

**Discovered:** 2026-02-11
**Resolved:** 2026-02-11 - Fixed in 86-02-FIX.md
**Commit:** dfc0e62
**Phase/Plan:** 86-02
**Severity:** Cosmetic
**Feature:** CompetitiveBadge display
**Description:** The badge showing Betpawa margin difference vs best competitor is hard to see
**Fix:** Added bg-red-100/bg-green-100 background colors, px-1.5 py-0.5 padding, semibold text

---

*Phase: 86-betpawa-vs-competitor-comparison*
*Plan: 02*
*Tested: 2026-02-11*
