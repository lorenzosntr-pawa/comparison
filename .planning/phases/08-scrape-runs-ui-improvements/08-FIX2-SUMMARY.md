# Summary: 08-FIX2 — Phase 8 UAT Issues Fix (Round 2)

## Overview

Fixed 3 remaining UAT issues from Phase 8 re-verification: SSE streaming missing platform_timings (major), dashboard widget progress bar colors not showing, and status badge update delay.

**Duration:** 8 min
**Commits:** 2

## What Changed

### Task 1: Fix UAT-006 — SSE streaming saves platform_timings
**Commit:** cf152d8

The `/scrape/stream` SSE endpoint wasn't saving platform_timings to the database when scrapes completed. This caused the "Platform Breakdown" card on detail pages to show "No platform timing data available" for scrapes triggered via the dashboard widget.

**Root cause:** The `event_generator()` in `/scrape/stream` had a minimal finally block that only saved `status` and `completed_at`, while the POST `/scrape` endpoint saved complete data including `platform_timings`.

**Changes:**
- Added `duration_ms: int | None = None` field to `ScrapeProgress` schema
- Updated orchestrator's `scrape_with_progress()` to include `duration_ms` in completed progress events
- Rewrote `/stream` endpoint's `event_generator()` to:
  - Accumulate `platform_timings` from progress events during scrape
  - Track total events count and failure count
  - Determine correct final status (completed/partial/failed)
  - Save complete `ScrapeRun` data in finally block

**Files:** src/scraping/schemas.py, src/scraping/orchestrator.py, src/api/routes/scrape.py

### Task 2: Fix UAT-004 — Dashboard widget progress bar colors
**Commit:** 4fd4e60

The progress bar on the dashboard widget wasn't showing platform-specific colors (green→blue→orange) during active scraping, even though the detail page worked correctly.

**Root cause:** The color condition excluded `phase === 'completed'` but this also filtered out per-platform completion events (where platform is set). Only the overall completion (platform is null) should show green.

**Changes:**
- Modified Progress className conditions to:
  - Only apply green/red for overall completion (when `platform` is null)
  - Apply platform colors for all events where `platform` is set (including per-platform completion)

**Files:** web/src/features/dashboard/components/recent-runs.tsx

### Task 3: Fix UAT-005 — Dashboard widget status badge sync
**Commit:** 4fd4e60

The status badge in the Recent Runs list still had a small delay updating from "running" to "completed" after the progress bar showed completion.

**Root cause:** Even with `refetchQueries`, there's a brief network delay before the UI updates. The database might also not have committed when the SSE completion event fires.

**Changes:**
- Added optimistic cache update via `queryClient.setQueryData()` before refetch
- Only trigger completion handling on overall completion (when `platform` is null)
- Badge now updates instantly when progress shows completion, then accurate data loads via refetch

**Files:** web/src/features/dashboard/components/recent-runs.tsx

## Technical Notes

### SSE Progress Event Flow
The orchestrator now emits progress events with timing data:
1. `phase="scraping"` with `platform` set — scraping started for platform
2. `phase="storing"` with `platform` set — storing events for platform
3. `phase="completed"` with `platform` set and `duration_ms` — platform finished
4. `phase="completed"` with `platform=None` — overall scrape finished

The `/stream` endpoint accumulates data from events where `phase="completed"` and `platform` is set, then saves the accumulated `platform_timings` when the overall completion event arrives.

### Optimistic Updates Pattern
```tsx
// Immediately update cache
queryClient.setQueryData(['scheduler-history'], (old) => ({
  ...old,
  runs: old.runs.map((run, i) =>
    i === 0 ? { ...run, status: newStatus } : run
  ),
}))
// Then fetch accurate data
void queryClient.refetchQueries({ queryKey: ['scheduler-history'] })
```

## Verification

- [x] `cd web && npm run build` succeeds
- [x] Platform Breakdown card shows data on detail page after SSE-triggered scrape
- [x] Progress bar shows platform-specific colors on dashboard widget
- [x] Status badge updates immediately on dashboard widget

## Issues Resolved

| ID | Title | Severity |
|----|-------|----------|
| UAT-004 | Dashboard widget progress bar not showing platform colors | Minor |
| UAT-005 | Dashboard widget status badge still has delay | Minor |
| UAT-006 | SSE streaming doesn't save platform_timings | Major |

## Next Steps

Ready for final verification with `/gsd:verify-work 8`. All known Phase 8 issues have been addressed.
