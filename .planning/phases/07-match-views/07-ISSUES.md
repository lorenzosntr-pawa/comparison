# UAT Issues: Phase 7 Match Views

**Tested:** 2026-01-21
**Source:** .planning/phases/07-match-views/07-02-SUMMARY.md
**Tester:** User via /gsd:verify-work (during Phase 7.1 testing)

## Open Issues

[None]

## Resolved Issues

### UAT-001: Match list table doesn't display inline odds columns

**Discovered:** 2026-01-21 during Phase 7.1 verification
**Resolved:** 2026-01-21 via 07-02-FIX.md
**Phase/Plan:** 07-02
**Severity:** Major
**Feature:** Match list view inline odds display
**Description:** The match list table did not display inline odds columns (1X2, O/U 2.5, BTTS) even though the API returned `inline_odds` data correctly.
**Root cause:** Frontend MARKET_CONFIG used incorrect market IDs (1, 18, 29) instead of Betpawa taxonomy IDs (3743, 5000, 3795).
**Resolution:** Updated frontend MARKET_CONFIG and AVAILABLE_COLUMNS in match-table.tsx and use-column-settings.ts to use Betpawa market IDs.
**Commit:** da806ee

---

*Phase: 07-match-views*
*Plan: 02*
*Tested: 2026-01-21*
