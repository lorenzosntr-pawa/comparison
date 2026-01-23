---
phase: 14-scraping-logging-workflow
plan: 14-FIX
type: fix
---

<objective>
Fix 3 UAT issues from Phase 14 verification.

Source: 14-ISSUES.md
Priority: 1 blocker, 1 major, 1 minor
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/14-scraping-logging-workflow/14-ISSUES.md

**Original plans for reference:**
@.planning/phases/14-scraping-logging-workflow/14-03-SUMMARY.md
@.planning/phases/14-scraping-logging-workflow/14-04-SUMMARY.md

**Key source files:**
@web/src/features/scrape-runs/hooks/use-scrape-progress.ts
@web/src/features/scrape-runs/detail.tsx
@web/src/features/dashboard/hooks/use-observe-scrape.ts
@web/src/features/dashboard/components/recent-runs.tsx
@src/scraping/clients/sportybet.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix UAT-002 (Blocker) - Detail page triggers unintended scrapes</name>
  <files>web/src/features/scrape-runs/hooks/use-scrape-progress.ts</files>
  <action>
**Root cause:** The `useScrapeProgress` hook in the scrape-runs feature connects to `/api/scrape/stream` which is the endpoint that CREATES and STARTS a new scrape. It should instead OBSERVE an existing scrape.

**The fix:**
1. Modify `useScrapeProgress` hook to use the run-specific observe endpoint:
   - Change from: `new EventSource('/api/scrape/stream')`
   - Change to: `new EventSource(\`/api/scrape/runs/\${runId}/progress\`)`

2. The hook already receives `runId` as a parameter, so this change is straightforward.

3. Handle the 410 Gone response gracefully - this occurs when the scrape is already completed:
   - The observe endpoint returns 410 if the scrape isn't running
   - Treat this as "scrape already completed, no need to stream"
   - Don't show an error, just don't connect

4. Reference the existing `useObserveScrape` hook in `web/src/features/dashboard/hooks/use-observe-scrape.ts` for the correct pattern - it already does this correctly.

**Do NOT change:**
- The dashboard's `startScrape` function in recent-runs.tsx - that intentionally creates new scrapes when user clicks "Start New Scrape" button
- The overall hook API/return values - keep isConnected, currentProgress, platformProgress, overallPhase
  </action>
  <verify>
1. Start a scheduled scrape (or trigger one from dashboard)
2. Navigate to detail page while scrape is running
3. Check backend logs: should see ONLY ONE scrape_run_id, not multiple
4. Detail page should show progress without spawning new scrapes
  </verify>
  <done>Detail page observes existing scrapes without creating new ones; only one scrape runs at a time</done>
</task>

<task type="auto">
  <name>Task 2: Fix UAT-001 (Major) - Platform status icons wrong for SB/B9</name>
  <files>web/src/features/dashboard/components/recent-runs.tsx</files>
  <action>
**Root cause:** The `getPlatformStatuses()` function derives platform status from `platform_timings`. However, this may have been a secondary effect of UAT-002 (cascade scrapes corrupting data) or an issue with how platform_timings is populated.

**After fixing UAT-002, verify if this issue persists:**

1. First, check if UAT-002 fix resolves this naturally (cascade scrapes were likely corrupting platform_timings data)

2. If issue persists, investigate the `getPlatformStatuses()` function:
   ```typescript
   function getPlatformStatuses(
     run: { status: string; platform_timings: Record<string, unknown> | null },
     isCurrentlyRunning: boolean,
     activeProgress: ScrapeProgressEvent | null
   )
   ```

3. Verify the logic:
   - If `run.platform_timings?.[platform]` exists → 'completed' ✓
   - If running and activeProgress matches platform → 'active' ✓
   - If running and no match → 'pending' ✓
   - If failed/partial and not in timings → 'failed' ✓

4. Check if the API response (`platform_timings` field from scheduler history) is populated correctly:
   - Read the backend code that populates `platform_timings` in scheduler.py
   - Verify SportyBet and Bet9ja timings are being included

5. If `platform_timings` is not being populated for SB/B9:
   - Check `src/api/routes/scheduler.py` history endpoint
   - Ensure `platform_timings` includes all platforms that completed

Note: This task may require minimal changes if UAT-002 fix resolves the data corruption. Document findings in summary.
  </action>
  <verify>
1. Complete a full scrape (all 3 platforms)
2. Go to dashboard
3. Check Recent Scrape Runs widget
4. Verify: BP, SB, B9 all show correct status (completed icons for successful platforms)
  </verify>
  <done>All three platform status icons accurately reflect completion state</done>
</task>

<task type="auto">
  <name>Task 3: Fix UAT-003 (Minor) - SportyBet schema validation errors</name>
  <files>src/scraping/clients/sportybet.py</files>
  <action>
**Root cause:** SportyBet API response format has changed - some markets now omit `farNearOdds`, `rootMarketId`, and `nodeMarketId` fields that were previously required in the Pydantic model.

**The fix:**
1. Locate the SportyBet market Pydantic model (likely in sportybet.py or a schemas file)

2. Make these fields optional:
   - `farNearOdds: ... | None = None`
   - In nested `marketExtendVOS` items:
     - `rootMarketId: ... | None = None`
     - `nodeMarketId: ... | None = None`

3. Ensure the code that uses these fields handles None gracefully:
   - Check where farNearOdds is accessed
   - Check where rootMarketId/nodeMarketId are accessed
   - Add null checks if accessing these values

4. This is defensive - the scrape already succeeds (1013 events stored) but logs are noisy with validation warnings.

**Impact:** Reduces log noise, prevents potential future failures if SportyBet removes these fields entirely.
  </action>
  <verify>
1. Run a scrape that includes SportyBet
2. Check backend logs
3. Verify: No "Field required" validation errors for farNearOdds, rootMarketId, nodeMarketId
4. Verify: SportyBet events are still scraped and stored correctly
  </verify>
  <done>SportyBet schema handles optional fields; no validation errors in logs</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Fixed 3 UAT issues: cascade scraping (blocker), platform status icons (major), SportyBet schema (minor)</what-built>
  <how-to-verify>
    1. Start backend: `uvicorn src.main:app --reload`
    2. Start frontend: `cd web && pnpm dev`
    3. **Test UAT-002 fix (blocker):**
       - Go to Dashboard
       - Click "Start New Scrape" button
       - Navigate to the scrape detail page while it's running
       - Watch backend logs: should see only ONE scrape_run_id
       - Detail page should update without spawning new scrapes
    4. **Test UAT-001 fix (major):**
       - Wait for scrape to complete
       - Go back to Dashboard
       - Look at Recent Scrape Runs widget
       - Verify BP, SB, B9 all show green checkmarks for completed run
    5. **Test UAT-003 fix (minor):**
       - Check backend logs during SportyBet phase
       - Verify no "Field required" errors for farNearOdds, marketExtendVOS fields
       - Verify SportyBet events are still stored (check events count)
  </how-to-verify>
  <resume-signal>Type "approved" if all issues are fixed, or describe remaining problems</resume-signal>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] UAT-002 (Blocker): Detail page no longer triggers new scrapes
- [ ] UAT-001 (Major): All platform status icons show correct state
- [ ] UAT-003 (Minor): No SportyBet schema validation errors
- [ ] Human verified all fixes
- [ ] No regressions - existing functionality still works
</verification>

<success_criteria>
- All UAT issues from 14-ISSUES.md addressed
- Backend logs show single scrape_run_id during scrape
- Platform status icons work correctly for all 3 platforms
- SportyBet scraping has clean logs
- Ready for re-verification
</success_criteria>

<output>
After completion, create `.planning/phases/14-scraping-logging-workflow/14-FIX-SUMMARY.md`
</output>
