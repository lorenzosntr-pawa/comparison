# Summary: 86-01-FIX — Fix UAT Issues

**Phase**: 86-betpawa-vs-competitor-comparison
**Plan**: 86-01-FIX
**Status**: Complete
**Completed**: 2026-02-11

## Objective

Fix 4 UAT issues from plan 86-01:
- UAT-003 (Blocker): Bookmaker toggle buttons missing from Historical Analysis page
- UAT-001 (Major): Best Comp column doesn't react to toggle selection
- UAT-004 (Minor): Competitive badge only on 1X2 - user wants on all markets
- UAT-002 (Major): Missing 1X2 margin data - backend issue (deferred)

## Changes

### Task 1-3: Integrate BookmakerFilter and Fix Toggle Visibility

**Files modified:**
- `web/src/features/historical-analysis/components/filter-bar.tsx`
- `web/src/features/historical-analysis/index.tsx`
- `web/src/features/historical-analysis/components/tournament-list.tsx`

**Changes:**
1. Added BookmakerFilter import and rendering in FilterBar
2. Added `selectedBookmakers` and `onBookmakersChange` props to FilterBar
3. Added `selectedBookmakers` state to HistoricalAnalysisPage
4. Wired `selectedBookmakers` through TournamentList → TournamentCard → MarketBreakdown
5. Dynamic competitor column header based on selection:
   - 2 competitors selected: "Best Comp."
   - 1 competitor selected: Shows that competitor's name (SportyBet/Bet9ja)
   - 0 competitors selected: Column hidden entirely
6. Competitive badge now appears on all market rows (1X2, O/U 2.5, BTTS, DC)
7. Badge visibility tied to competitor selection

**Commit:** 717fa18

### Task 4: Document UAT-002 as Deferred

**File modified:**
- `.planning/phases/86-betpawa-vs-competitor-comparison/86-01-ISSUES.md`

**Changes:**
- Created "Deferred Issues" section
- Moved UAT-002 to Deferred with rationale (backend fix out of scope)
- Moved UAT-001, UAT-003, UAT-004 to Resolved Issues with commit reference

## Verification

- [x] Build succeeds: `npm run build` passes
- [x] Bookmaker toggle buttons visible on Historical Analysis page
- [x] Toggling bookmakers affects column header text
- [x] Toggling all competitors off hides the competitor column
- [x] Competitive badge appears on all 4 market rows
- [x] ISSUES.md documents deferred item

## Issues

### Resolved
- UAT-003 (Blocker): Fixed — Toggle buttons now visible
- UAT-001 (Major): Fixed — Toggle has visible effect on display
- UAT-004 (Minor): Fixed — Badge on all market rows

### Deferred
- UAT-002 (Major): Backend fix required — `_build_inline_odds()` in src/api/routes/events.py needs modification to include markets with empty outcomes

## Next Steps

- Plan 86-02, 86-03 already complete
- Continue to 86-04: Difference chart toggle
- Or re-verify 86-01 fixes before proceeding
