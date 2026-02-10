---
phase: 81-interactive-chart
plan: FIX
type: fix
---

<objective>
Fix 2 UAT blocker issues from Phase 81 verification.

Source: 81-ISSUES.md
Priority: 2 blockers (click-to-lock persistence, comparison mode bookmaker display)

Purpose: Make click-to-lock actually work by debugging why recharts onClick isn't triggering lock state changes, and fix comparison mode to show all bookmaker data.
Output: Working click-to-lock functionality and complete comparison mode display.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/81-interactive-chart/81-ISSUES.md

**Original plan for reference:**
@.planning/phases/81-interactive-chart/81-01-PLAN.md

**Previous fix attempt:**
@.planning/phases/81-interactive-chart/81-01-FIX-SUMMARY.md

**Key source files:**
@web/src/features/matches/hooks/use-chart-lock.ts
@web/src/features/matches/components/odds-line-chart.tsx
@web/src/features/matches/components/margin-line-chart.tsx
@web/src/features/matches/components/market-history-panel.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Debug and fix click-to-lock event handling (UAT-001)</name>
  <files>web/src/features/matches/hooks/use-chart-lock.ts, web/src/features/matches/components/odds-line-chart.tsx</files>
  <action>
The click handler expects `data.activeTooltipIndex` from recharts onClick, but recharts may not always provide this property. The previous fix added debounce and refs but the fundamental event data extraction may be failing.

**Debug approach:**

1. Add console.log in handleChartClick to see what recharts actually passes:
```typescript
console.log('Chart click event:', JSON.stringify(data, null, 2))
```

2. Run app, click chart, check browser console to see actual event shape.

**Likely fixes based on recharts documentation:**

Option A: If `activeTooltipIndex` is undefined, use `activeTooltipPayload` index:
- recharts onClick provides `activeTooltipPayload` array
- The clicked point's index can be found by checking the first payload item

Option B: Extract index from chart data by matching time:
- Get `time` from `data.activePayload[0].payload.time`
- Find index in chartData array where `chartData[i].time === time`
- Pass chartData to the hook or use a callback pattern

Option C: Use recharts' `onMouseUp` instead of `onClick`:
- Some recharts versions have issues with onClick
- onMouseUp fires more reliably

**Implementation (apply chosen fix):**

After debugging, update use-chart-lock.ts:
- Fix the event data extraction to reliably get both time and index
- Ensure state actually changes (useState calls trigger re-render)
- Add defensive logging to track state changes

Update odds-line-chart.tsx:
- Ensure handleChartClick is passed correctly to LineChart onClick
- Verify the hook is being used correctly

Verify the fix works before moving to Task 2.

DO NOT just guess - actually debug to understand why it's not working.
  </action>
  <verify>
1. `cd web && npm run dev`
2. Open odds history dialog
3. Click on chart point
4. Confirm: Red reference line appears and stays visible
5. Confirm: Comparison panel appears below chart with locked values
6. Move mouse - reference line stays fixed
  </verify>
  <done>Click-to-lock persists on OddsLineChart - reference line and comparison panel visible after click</done>
</task>

<task type="auto">
  <name>Task 2: Apply click-to-lock fix to MarginLineChart and MarketHistoryPanel</name>
  <files>web/src/features/matches/components/margin-line-chart.tsx, web/src/features/matches/components/market-history-panel.tsx</files>
  <action>
Apply the same fix pattern from Task 1 to the other chart components.

**MarginLineChart:**
- Same hook usage as OddsLineChart
- Apply same event handling fix

**MarketHistoryPanel:**
- Uses inline click handler (not the hook)
- Fix the same event data extraction pattern
- Ensure synchronized lock works across mini-charts

Test each component individually to confirm fix works.
  </action>
  <verify>
1. Open margin history - click-to-lock works
2. Open full market view - click any mini-chart
3. All mini-charts show locked line at same timestamp
4. Comparison table appears below with all outcome values
  </verify>
  <done>Click-to-lock works on all three chart types</done>
</task>

<task type="auto">
  <name>Task 3: Fix comparison mode bookmaker data display (UAT-002)</name>
  <files>web/src/features/matches/components/odds-line-chart.tsx</files>
  <action>
The comparison mode data merge in chartData useMemo only shows data when timestamps match exactly across bookmakers.

**Root cause analysis:**
Each bookmaker's data has different `captured_at` timestamps because scraping happens at different times. The current merge:
```typescript
const time = point.captured_at
if (!timeMap.has(time)) {
  timeMap.set(time, {})
}
```
Only creates rows for timestamps that exist - if Betpawa has data at 10:00:05 and SportyBet at 10:00:12, they go in separate rows.

**Fix approach:**

Option A: Bucket timestamps to nearest minute or 5-minutes:
```typescript
const bucketTime = (iso: string) => {
  const d = new Date(iso)
  d.setSeconds(0, 0) // Round to minute
  return d.toISOString()
}
```
Then merge data into buckets.

Option B: Use forward-fill interpolation:
- Create unified timeline from all bookmakers
- For each time point, use last known value for each bookmaker
- This is more complex but provides continuous data

Option C: Show separate lines per bookmaker (current approach) but improve tooltip:
- Keep data as-is (separate timestamps)
- Tooltip already shows values at hover position
- The issue might just be tooltip formatting, not data

**Implementation:**
Most likely Option A is the right balance - bucket to nearest minute. This groups data from all bookmakers at approximately the same time into single data points.

Update the comparison mode chartData transform to:
1. Normalize timestamps to nearest minute
2. Merge all bookmaker values at that bucketed time
3. Show dashes or interpolated values for missing data points

Also verify the Tooltip formatter correctly displays all bookmaker values.
  </action>
  <verify>
1. Enable comparison mode in history dialog
2. Move cursor along chart
3. Tooltip shows values for ALL bookmakers (Betpawa, SportyBet, Bet9ja)
4. Some may show "-" if no data at that time point, but all should be present
  </verify>
  <done>Comparison mode tooltip shows all bookmaker values at each time point</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Fixed click-to-lock and comparison mode display</what-built>
  <how-to-verify>
    1. Run: `cd web && npm run dev`
    2. Open Odds Comparison page
    3. Click any odds value to open history dialog

    **Test click-to-lock (UAT-001):**
    4. Click on a point in the chart
    5. Verify: Red vertical reference line appears
    6. Verify: Comparison panel appears below chart showing locked values
    7. Move mouse around - line and panel stay fixed
    8. Click same point or "Unlock" - releases lock

    **Test comparison mode (UAT-002):**
    9. Enable "Compare bookmakers" toggle
    10. Move cursor along chart
    11. Verify: Tooltip shows values for ALL bookmakers (not just Betpawa)

    **Test other charts:**
    12. Check margin history - click-to-lock works
    13. Enable "Show all outcomes" - click any mini-chart
    14. All mini-charts show synchronized lock
  </how-to-verify>
  <resume-signal>Type "approved" if both issues fixed, or describe remaining problems</resume-signal>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] UAT-001 resolved: Click-to-lock persists on all chart types
- [ ] UAT-002 resolved: Comparison mode shows all bookmaker values
- [ ] `cd web && npx tsc --noEmit` passes
- [ ] `cd web && npm run build` succeeds
- [ ] No console errors during chart interactions
</verification>

<success_criteria>
- All UAT issues from 81-ISSUES.md addressed
- Click-to-lock works reliably on OddsLineChart, MarginLineChart, MarketHistoryPanel
- Comparison mode tooltip displays all bookmakers
- User verification passes
- Ready for re-verification or Phase 82
</success_criteria>

<output>
After completion, create `.planning/phases/81-interactive-chart/81-FIX-SUMMARY.md`

Update 81-ISSUES.md:
- Move resolved issues to "Resolved Issues" section
- Include fix description and commit hash
</output>
