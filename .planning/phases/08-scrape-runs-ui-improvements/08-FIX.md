---
phase: 08-scrape-runs-ui-improvements
plan: FIX
type: fix
---

<objective>
Fix 3 UAT issues from Phase 8 testing.

Source: 08-ISSUES.md
Priority: 0 critical, 0 major, 3 minor
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/08-scrape-runs-ui-improvements/08-ISSUES.md

**Original plan for reference:**
@.planning/phases/08-scrape-runs-ui-improvements/08-01-PLAN.md

**Key files to understand:**
@web/src/features/scrape-runs/components/live-progress.tsx
@web/src/features/dashboard/components/recent-runs.tsx
@web/src/features/scrape-runs/detail.tsx
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix UAT-001 - Add platform-specific colors to progress bars</name>
  <files>web/src/features/dashboard/components/recent-runs.tsx</files>
  <action>
The dashboard RecentRuns widget uses a single Progress component without platform-specific colors. The SSE events contain platform info but the progress bar doesn't reflect it.

Fix approach:
1. In RecentRuns, track the current platform from activeProgress
2. Apply platform-specific color classes to the Progress component based on current platform:
   - betpawa: green (e.g., `[&>div]:bg-green-500`)
   - sportybet: blue (e.g., `[&>div]:bg-blue-500`)
   - bet9ja: orange (e.g., `[&>div]:bg-orange-500`)
3. Use cn() to dynamically apply the color class based on `activeProgress?.platform`

The LiveProgressPanel component already has PLATFORM_COLORS defined and uses them in the per-platform progress section. Ensure consistent color mapping.
  </action>
  <verify>Start a scrape from dashboard, verify progress bar color changes as each platform is scraped (green → blue → orange)</verify>
  <done>Progress bar shows platform-specific color matching current scraping platform</done>
</task>

<task type="auto">
  <name>Task 2: Fix UAT-002 - Improve status sync between progress and list</name>
  <files>web/src/features/dashboard/components/recent-runs.tsx</files>
  <action>
The status badge in the runs list doesn't update immediately when progress shows completed. This is because:
1. Query invalidation happens asynchronously
2. The list still shows old "running" status until refetch completes

Fix approach:
1. After scrape completes (phase === 'completed'), use `queryClient.setQueryData` to optimistically update the most recent run's status to 'completed' immediately
2. Still perform invalidateQueries for full refetch, but the optimistic update provides instant visual feedback
3. When isStreaming becomes false and phase is 'completed', also trigger an immediate refetch with `{ cancelRefetch: false }`

Alternative simpler fix:
- Call `refetch()` synchronously right after closing the EventSource, and await it
- Use `await queryClient.refetchQueries({ queryKey: ['scheduler-history'] })` instead of just invalidate

Choose the simpler approach first: use refetchQueries with await to ensure data is updated before the loading state clears.
  </action>
  <verify>Complete a scrape, verify the list badge updates to 'completed' at the same moment the progress bar shows completion</verify>
  <done>Status badge updates simultaneously with progress bar completion, no visible delay</done>
</task>

<task type="auto">
  <name>Task 3: Fix UAT-003 - Add live progress bars to detail page</name>
  <files>web/src/features/scrape-runs/detail.tsx, web/src/features/scrape-runs/components/live-progress.tsx</files>
  <action>
The detail page shows only a text indicator when a scrape is running. User wants the actual per-platform progress bars like in the dashboard widget.

Fix approach:
1. Import LiveProgressPanel into ScrapeRunDetailPage
2. Replace the current simple "in progress" Card (lines 159-172) with LiveProgressPanel component
3. Pass `showOnlyWhenActive={true}` so it only renders when there's an active scrape
4. Add `onComplete` callback to refetch the run detail data when scrape finishes

However, there's a design consideration: LiveProgressPanel starts a NEW scrape when mounted (it triggers the SSE stream). For viewing an existing running scrape, we need a different approach.

Better fix:
1. Create a new component or mode in LiveProgressPanel that OBSERVES an existing scrape rather than starting one
2. OR use the same useActiveScrapesObserver hook that RecentRuns uses to passively observe
3. Import useActiveScrapesObserver into detail page
4. Create a mini progress panel that shows per-platform progress using the observer data

Simplest fix that matches what user expects:
1. The detail page already polls when running (`pollWhileRunning: true`)
2. Add per-platform progress indicators based on `platform_timings` data that updates via polling
3. Show animated progress bars for platforms not yet in timings
4. This provides visual progress without requiring SSE connection

Implementation:
1. In detail.tsx, replace the simple "in progress" indicator with a more visual progress section
2. Show all 3 platforms with progress bars
3. Platforms in `platform_timings` = complete (100%, green)
4. Platforms not in timings = in progress (animated, with estimated progress based on scrape order)
5. Use the same PLATFORM_COLORS pattern from LiveProgressPanel
  </action>
  <verify>Navigate to detail page while a scrape is running, verify per-platform progress bars are visible and update as each platform completes</verify>
  <done>Detail page shows per-platform progress bars during active scrapes, matching the dashboard widget visual style</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] `cd web && npm run build` succeeds without errors
- [ ] Progress bars show platform-specific colors in dashboard
- [ ] Status badge syncs immediately with progress bar completion
- [ ] Detail page shows per-platform progress bars for running scrapes
</verification>

<success_criteria>
- All 3 UAT issues from 08-ISSUES.md addressed
- Build passes
- Ready for re-verification with /gsd:verify-work 8
</success_criteria>

<output>
After completion, create `.planning/phases/08-scrape-runs-ui-improvements/08-FIX-SUMMARY.md`
</output>
