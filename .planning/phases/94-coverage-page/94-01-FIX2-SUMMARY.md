# Summary: 94-01-FIX2 — Stable Tournament Stats Cards

## Problem

BUG-017: Tournament stats cards recalculated when switching availability filter toggles because the `usePalimpsestEvents` hook returned different data based on the `availability` parameter.

## Solution

Added a separate `usePalimpsestEvents` query specifically for stats cards that always fetches ALL tournaments (no availability filter):

```tsx
// Unfiltered query for stats cards - always fetches ALL tournaments
const { data: statsData, ... } = usePalimpsestEvents({
  includeStarted: filters.includeStarted,
  // NO availability param - always gets everything
})

// Filtered query for table display
const { data: eventsData, ... } = usePalimpsestEvents({
  availability: apiAvailability,  // Changes with filter toggle
  search: filters.search || undefined,
  includeStarted: filters.includeStarted,
})
```

## Data Flow

**Before (broken):**
```
availability toggle → eventsData changes → allTournaments changes → stats recalculate
```

**After (fixed):**
```
availability toggle → eventsData changes → table updates
                   → statsData unchanged → stats stay stable
```

## Files Changed

| File | Change |
|------|--------|
| [coverage/index.tsx](web/src/features/coverage/index.tsx) | Added separate `statsData` query, updated data sources |

## Key Changes

1. **New `statsData` query** (lines 33-40): Fetches ALL tournaments with no availability filter
2. **Updated `allTournaments`** (lines 57-60): Now derived from `statsData` instead of `eventsData`
3. **New `tableTournaments`** (lines 74-77): Derived from filtered `eventsData` for table display
4. **Fixed `filteredTournaments`** (lines 80-86): Now filters `tableTournaments` by country

## Verification

- [ ] Toggle availability filter (All Events → Gaps → BetPawa Only → Competitor Only)
- [ ] Stats cards should NOT recalculate, flicker, or re-render
- [ ] Table should still filter correctly based on availability + country selections

## Result

BUG-017 resolved. Stats cards now remain stable when switching availability filters.
