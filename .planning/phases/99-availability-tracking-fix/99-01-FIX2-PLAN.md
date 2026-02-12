---
phase: 99-availability-tracking-fix
plan: 01-FIX2
type: fix
---

<objective>
Fix 2 UAT issues from plan 99-01-FIX.

Source: 99-01-FIX-ISSUES.md
Priority: 0 critical, 1 major, 1 cosmetic
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/99-availability-tracking-fix/99-01-FIX-ISSUES.md

**Original plan for reference:**
@.planning/phases/99-availability-tracking-fix/99-01-FIX-PLAN.md

**Key files:**
@web/src/features/matches/components/match-table.tsx (Odds Comparison page - has the issues)
@web/src/features/matches/components/odds-badge.tsx (Event Details reference implementation)
</context>

<tasks>

<task type="auto">
  <name>Fix UAT-004: Hide margin when market unavailable</name>
  <files>web/src/features/matches/components/match-table.tsx</files>
  <action>
Modify the MarginValue component to accept and check availability state.

1. Add `available` and `unavailableSince` props to MarginValue component interface
2. When `available === false`, render strikethrough dash with tooltip (matching OddsValue pattern)
3. Update MarginValue calls in the render loop to pass availability from the market

The margin should show as unavailable when the underlying market's `available` field is false.

Key change in MarginValue:
```typescript
// Add to function params
available?: boolean,
unavailableSince?: string | null,

// Add at start of function body, before the null check:
if (available === false) {
  const tooltipText = unavailableSince
    ? formatUnavailableSince(unavailableSince)
    : 'Market unavailable'
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="text-muted-foreground line-through text-xs cursor-help">-</span>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltipText}</p>
      </TooltipContent>
    </Tooltip>
  )
}
```

Also update the MarginValue call in the render loop to pass availability:
- Get the market for this marketId from bookmaker.inline_odds
- Pass `available={market?.available !== false}` and `unavailableSince={market?.unavailable_since}`
  </action>
  <verify>
1. Build succeeds: `cd web && npm run build`
2. When a competitor market is unavailable, the margin column shows strikethrough dash instead of calculated margin
  </verify>
  <done>Margin column shows "-" with strikethrough and tooltip when market is unavailable, not calculated margin values</done>
</task>

<task type="auto">
  <name>Fix UAT-003: Consistent unavailable styling on Odds Comparison</name>
  <files>web/src/features/matches/components/match-table.tsx</files>
  <action>
Review and ensure OddsValue unavailable styling matches OddsBadge from Event Details.

Current OddsValue (line 217-234) shows:
- `text-muted-foreground line-through text-xs cursor-help` for unavailable dash

OddsBadge shows:
- `text-muted-foreground line-through cursor-help` for unavailable dash (no text-xs because it's in a different context)

The styling IS consistent (strikethrough + muted + cursor-help). The user may have been comparing to the case where:
- OddsValue shows odds when available=false but odds !== null (Case 3 in OddsBadge)
- Need to verify this case is handled in OddsValue

Check if OddsValue handles the case: `available === false && odds !== null` (stale odds that became unavailable).

If not handled, add case for showing stale odds with strikethrough before the normal odds rendering (similar to OddsBadge lines 68-87).

Actually looking at the code again, OddsValue checks `!available` at line 217 BEFORE checking `odds === null` at line 237. This means:
- If available=false, it shows strikethrough dash regardless of whether there are stale odds
- This is DIFFERENT from OddsBadge which shows the stale odds with strikethrough

To match Event Details behavior:
1. When available=false AND odds !== null → show odds value with strikethrough styling
2. When available=false AND odds === null → show dash with strikethrough

Modify OddsValue to handle these cases like OddsBadge does.
  </action>
  <verify>
1. Build succeeds: `cd web && npm run build`
2. Visual inspection: unavailable markets on Odds Comparison show same styling as Event Details
  </verify>
  <done>Unavailable odds display with strikethrough styling matching Event Details page</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] All critical issues fixed (none)
- [ ] All major issues fixed (UAT-004)
- [ ] Minor/cosmetic issues fixed (UAT-003)
- [ ] Build passes without errors
- [ ] Original acceptance criteria from issues met
</verification>

<success_criteria>
- All UAT issues from 99-01-FIX-ISSUES.md addressed
- Build passes
- Ready for re-verification with /gsd:verify-work
</success_criteria>

<output>
After completion, create `.planning/phases/99-availability-tracking-fix/99-01-FIX2-SUMMARY.md`
</output>
