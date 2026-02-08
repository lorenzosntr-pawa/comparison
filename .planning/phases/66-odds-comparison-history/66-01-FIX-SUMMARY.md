# Fix Summary: 66-01-FIX

**Phase:** 66-odds-comparison-history
**Plan:** 66-01-FIX
**Completed:** 2026-02-08
**Issues Fixed:** 2 blockers

## Issues Addressed

| ID | Title | Severity | Status |
|----|-------|----------|--------|
| UAT-001 | Page crashes when clicking odds cell | Blocker | Resolved |
| UAT-002 | Page crashes when clicking margin cell | Blocker | Resolved |

## Root Cause Analysis

The page crash was caused by **missing React keys on Fragment elements** in `match-table.tsx`.

When mapping over `visibleMarkets` to render table cells, the code used empty fragments `<>...</>` without key props:

```tsx
// Before (broken)
{visibleMarkets.map((marketId) => (
  <>
    {MARKET_CONFIG[marketId].outcomes.map(...)}
    <th key={`${marketId}-margin`}>%</th>
  </>
))}
```

Without keys on the Fragment, React's reconciliation algorithm became confused when new components (HistoryDialog with Radix UI Tabs) were mounted. This caused an "Invalid hook call" error from @radix-ui/react-tabs, which crashed the entire page.

## Changes Made

### 1. match-table.tsx - Fragment Keys (Root Fix)
- Added `Fragment` import from React
- Changed `<>...</>` to `<Fragment key={marketId}>...</Fragment>` in both header and body map iterations
- This ensures React can properly reconcile the component tree when dialog opens

### 2. odds-line-chart.tsx - Defensive Null Checks
- Added optional chaining: `point.outcomes?.forEach()`
- Added null check: `if (!data.length || !data[0]?.outcomes?.length) return []`
- Added type guard on YAxis tickFormatter

### 3. margin-line-chart.tsx - Defensive Null Checks
- Added type guard on YAxis tickFormatter: `typeof value === 'number'`

### 4. history-dialog.tsx - Error Boundary
- Added `ChartErrorBoundary` class component to catch rendering errors
- Wrapped both chart components with error boundary
- Provides graceful fallback UI if chart fails to render

## Commits

- `97ec0d7` - fix(66-01): add defensive null checks to OddsLineChart
- `5756fe7` - fix(66-01): fix history dialog crash on click

## Verification

- [x] Clicking odds cell opens dialog without crash
- [x] Clicking margin cell opens dialog without crash
- [x] Dialog displays Odds tab with line chart
- [x] Dialog displays Margin tab with line chart
- [x] Row click navigation still works
- [x] Hover feedback on cells works
- [x] `npm run type-check` passes
- [x] `npm run build` succeeds

## Lessons Learned

1. **Always add keys to Fragments in `.map()` calls** - Even when child elements have keys, the Fragment wrapper needs its own key for proper reconciliation
2. **Check browser console, not server logs** - React errors appear in browser DevTools, not terminal
3. **Vite HMR cache can cause stale state** - Clear `node_modules/.vite` and restart dev server when debugging mysterious crashes

---

*Fix plan source: 66-01-FIX.md*
*Issues source: 66-01-ISSUES.md*
