# UAT Issues: Phase 99 Plan 01-FIX

**Tested:** 2026-02-12
**Source:** .planning/phases/99-availability-tracking-fix/99-01-FIX-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

### UAT-003: Odds Comparison page lacks strikethrough styling for unavailable odds

**Discovered:** 2026-02-12
**Phase/Plan:** 99-01-FIX
**Severity:** Cosmetic
**Feature:** Unavailable odds display on Odds Comparison page
**Description:** Unavailable odds on Odds Comparison page show as plain dash "-" without the strikethrough and grey styling that Event Details page has. User wants consistent visual treatment across both pages.
**Expected:** Unavailable odds should display with strikethrough styling and grey color (matching Event Details page)
**Actual:** Plain dash "-" displayed without any visual indication of unavailable state

### UAT-004: Margin still calculated for unavailable odds on Odds Comparison page

**Discovered:** 2026-02-12
**Phase/Plan:** 99-01-FIX
**Severity:** Major
**Feature:** Margin display for unavailable competitors
**Description:** When competitor odds are marked unavailable, the margin column still shows calculated margin values. This is functionally incorrect - margins should not be displayed when the underlying odds are unavailable.
**Expected:** Margin column should show "-" or be blank when competitor odds are unavailable
**Actual:** Margin values still calculated and displayed for unavailable competitor odds

## Resolved Issues

[None yet]

---

*Phase: 99-availability-tracking-fix*
*Plan: 01-FIX*
*Tested: 2026-02-12*
