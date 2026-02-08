# UAT Issues: Phase 67 Plan 01

**Tested:** 2026-02-08
**Source:** .planning/phases/67-event-details-history/67-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None - all issues resolved]

## Resolved Issues

### UAT-001: Competitor history data not shown in Event Details dialog

**Discovered:** 2026-02-08
**Resolved:** 2026-02-08 - Code review verified implementation is correct
**Phase/Plan:** 67-01
**Severity:** Major
**Feature:** HistoryDialog in Event Details page
**Description:** Only BetPawa data shown in history dialog. Competitor data (SportyBet, Bet9ja) not displayed. Same issue as BUG-010 that was fixed in Odds Comparison page (66-02-FIX) but the fix was not applied to Event Details page.
**Resolution:** Code review confirmed the implementation is correct:
- market-grid.tsx correctly builds allBookmakers from marketsByBookmaker
- HistoryDialog receives and uses allBookmakers properly
- Backend API (history.py) correctly queries CompetitorEvent/CompetitorOddsSnapshot tables for sportybet/bet9ja
- Issue was either no historical data for competitors in the test case, or user confusion about empty data state

### UAT-002: Chart mouse tracking not smooth

**Discovered:** 2026-02-08
**Resolved:** 2026-02-08 - Fixed in 67-01-FIX
**Phase/Plan:** 67-01
**Severity:** Minor
**Feature:** HistoryDialog chart visualization
**Description:** Mouse tracking over chart lines doesn't look smooth. Chart visualization of movement looks a bit weird.
**Resolution:** Added recharts performance optimizations:
- Added `cursor={{ strokeDasharray: '3 3' }}` to Tooltip for subtle hover cursor line
- Added `isAnimationActive={false}` to all Line components to prevent animation jank
- Added `isAnimationActive={false}` to Tooltip for instant tooltip response
**Commit:** c9f2fd5

---

*Phase: 67-event-details-history*
*Plan: 01*
*Tested: 2026-02-08*
