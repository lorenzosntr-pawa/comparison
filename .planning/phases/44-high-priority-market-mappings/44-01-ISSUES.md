# UAT Issues: Phase 44 Plan 01

**Tested:** 2026-02-02 (retest after 44-01-FIX)
**Source:** .planning/phases/44-high-priority-market-mappings/44-01-FIX-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved]

## Resolved Issues

### UAT-004: Merged market rows appear multiple times with identical data
**Resolved:** 2026-02-02 - Fixed in 44-01-FIX2.md
**Commit:** `4d2dcf6` - Iterate deduplicated map instead of raw API data

### UAT-001: HAOU market mapping mixes up Home/Away odds
**Resolved:** 2026-02-02 - Fixed in 44-01-FIX.md
**Commit:** `1836086` - Split Bet9ja HAOU into Home/Away O/U markets

### UAT-002: TMGHO/TMGAW UI display issues - duplicates and missing odds
**Resolved:** 2026-02-02 - Fixed in 44-01-FIX.md
**Commit:** `8939afa` - Merge split market outcomes in UI
**Note:** Partially resolved - outcomes now merge correctly, but see UAT-004 for remaining duplicate row issue

### UAT-003: Outcome incompatibility between platforms not handled gracefully
**Resolved:** 2026-02-02 - Documented as expected behavior
**Note:** Different platforms have incompatible outcome structures. Only directly comparable outcomes are shown.

---

*Phase: 44-high-priority-market-mappings*
*Plan: 01*
*Tested: 2026-02-02*
