# Phase 48-01-FIX2 Summary: Market Deduplication Fix

**Applied market deduplication logic to summary-section.tsx to match market-grid.tsx behavior**

## Performance

- **Duration**: ~5 min
- **Files Modified**: 1
- **Lines Changed**: +117, -49 (net +68)
- **Build**: Verified (npm run build passes)

## Accomplishments

### Task 1: Fix UAT-006 - Apply market deduplication before counting
- Added `mergeMarketOutcomes()` helper (copied from market-grid.tsx)
- Added `buildDeduplicatedMarkets()` to create merged market maps
- Updated `calculateMarketCoverage()` to use deduplicated markets
- Updated `calculateMappingStats()` to use deduplicated markets
- Updated `calculateCompetitiveStats()` to use pre-built deduplicated maps
- All three summary cards now use consistent deduplication

## Task Commits

1. `0fce350` - fix(48-01-FIX2): apply market deduplication to summary-section counts

## Files Modified

| File | Changes |
|------|---------|
| `web/src/features/matches/components/summary-section.tsx` | +117, -49 (deduplication logic) |

## Decisions Made

1. **Copy rather than extract**: Copied `mergeMarketOutcomes()` from market-grid.tsx instead of extracting to shared module. Keeps the fix simple and localized.
2. **Single deduplication pass**: Build deduplicated maps once in component, pass to all calculation functions via useMemo for efficiency.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Resolved

- [x] UAT-006: Betpawa market count now matches visible markets in grid

## Verification

- [x] `npm run build` in web/ succeeds without errors
- [x] Market deduplication logic matches market-grid.tsx
- [x] Ready for re-verification by user

---

*Phase: 48-event-summary-redesign*
*Plan: 48-01-FIX2*
*Completed: 2026-02-04*
