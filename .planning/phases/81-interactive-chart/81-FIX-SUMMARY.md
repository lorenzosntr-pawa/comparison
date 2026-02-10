# Summary: 81-FIX (Interactive Chart Fix)

**Phase:** 81-interactive-chart
**Plan:** FIX
**Status:** Complete
**Date:** 2026-02-10

## What Was Built

Fixed 2 blocker UAT issues from Phase 81 verification:

1. **Click-to-lock persistence** - Fixed recharts event handling to properly parse `activeTooltipIndex` as string and get time from chartData array
2. **Comparison mode multi-bookmaker display** - Added forward-fill logic so all bookmaker lines are visible at every time point

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Index parsing | Handle string/number | recharts provides activeTooltipIndex as string, not number |
| Time lookup | Use chartData array | activePayload is undefined in recharts onClick events |
| Data interpolation | Forward-fill | Carry forward last known value for each bookmaker |
| Time bucketing | Nearest minute | Merge data from different bookmakers captured at similar times |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| be6342e | fix | fix click-to-lock by parsing activeTooltipIndex as string |
| 37dc109 | fix | add forward-fill for comparison mode multi-bookmaker display |

## Files Changed

- `web/src/features/matches/hooks/use-chart-lock.ts` - Fixed event data parsing
- `web/src/features/matches/components/odds-line-chart.tsx` - Added forward-fill
- `web/src/features/matches/components/margin-line-chart.tsx` - Added forward-fill

## Issues Resolved

- [x] UAT-001: Click-to-lock doesn't persist on any chart type
- [x] UAT-002: Comparison mode doesn't show all bookmakers

## Technical Details

### UAT-001 Root Cause

recharts `onClick` callback provides `activeTooltipIndex` as a **string** (e.g., `'82'`), not a number. The original code:
```typescript
if (typeof data.activeTooltipIndex === 'number') { ... }
```
Always evaluated to false. Additionally, `data.activePayload` was undefined.

### UAT-001 Fix

Parse activeTooltipIndex from either format and use chartData for time lookup:
```typescript
const parsed = typeof data.activeTooltipIndex === 'number'
  ? data.activeTooltipIndex
  : parseInt(String(data.activeTooltipIndex), 10)

// Get time from chartData using the index
if (chartData && index >= 0 && index < chartData.length) {
  time = chartData[index].time
}
```

### UAT-002 Root Cause

Each bookmaker's scraper runs at different times, producing different `captured_at` timestamps. Without interpolation, data points only contained values for whichever bookmaker happened to have data at that exact time.

### UAT-002 Fix

Added forward-fill logic to both chart components:
```typescript
const lastKnown: Record<string, number | null> = {}
const filledData = sortedEntries.map(([time, values]) => {
  // Update last known values
  for (const slug of allBookmakers) {
    if (values[slug] !== undefined && values[slug] !== null) {
      lastKnown[slug] = values[slug]
    }
  }
  // Build row with forward-filled values
  const filledRow: Record<string, number | null> = {}
  for (const slug of allBookmakers) {
    filledRow[slug] = values[slug] ?? lastKnown[slug] ?? null
  }
  return { time, timeLabel, ...filledRow }
})
```

## Verification

- [x] Click-to-lock persists on OddsLineChart
- [x] Click-to-lock persists on MarginLineChart
- [x] Comparison mode shows all bookmakers on OddsLineChart
- [x] Comparison mode shows all bookmakers on MarginLineChart
- [x] User verified both fixes working

## Next Steps

Phase 81 complete. Ready for Phase 82 or next milestone.
