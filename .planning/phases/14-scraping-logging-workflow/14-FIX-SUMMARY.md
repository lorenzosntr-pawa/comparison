---
phase: 14-scraping-logging-workflow
plan: FIX
subsystem: scraping, ui
tags: [sse, pydantic, sportybet, react-hooks, eventSource]

# Dependency graph
requires:
  - phase: 14-04
    provides: scrape detail page, SSE streaming
provides:
  - Fixed cascade scrape bug (detail page no longer triggers new scrapes)
  - Correct platform status icons
  - Clean SportyBet validation logs
affects: [scrape-runs, dashboard]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Observe endpoint pattern for SSE (vs stream endpoint that creates)
    - Optional Pydantic fields for evolving external APIs

key-files:
  created: []
  modified:
    - web/src/features/scrape-runs/hooks/use-scrape-progress.ts
    - src/market_mapping/types/sportybet.py

key-decisions:
  - "UAT-001 platform icons required no code fix - root cause was UAT-002 cascade scrapes"
  - "Use observe endpoint /api/scrape/runs/{id}/progress instead of /api/scrape/stream"
  - "Make SportyBet schema fields optional to handle API format changes"

patterns-established:
  - "SSE observe vs create: use run-specific endpoints to observe, generic /stream to create"

issues-created: []

# Metrics
duration: 6min
completed: 2026-01-22
---

# Phase 14 FIX: UAT Bug Fixes Summary

**Fixed 3 UAT issues: cascade scraping blocker, platform status icons, SportyBet schema validation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-22T15:30:00Z
- **Completed:** 2026-01-22T15:36:00Z
- **Tasks:** 4 (3 auto + 1 verify)
- **Files modified:** 2

## Accomplishments

- Fixed cascade scrape bug (UAT-002 Blocker) - detail page now observes instead of creating new scrapes
- Verified platform status icon logic (UAT-001 Major) - no code changes needed, issue was caused by UAT-002
- Made SportyBet schema fields optional (UAT-003 Minor) - eliminates validation errors for API format changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix UAT-002 cascade scrapes** - `bbcace7` (fix)
2. **Task 2: Verify UAT-001 platform icons** - No commit (investigation only - root cause was UAT-002)
3. **Task 3: Fix UAT-003 SportyBet schema** - `f096612` (fix)

## Files Created/Modified

- `web/src/features/scrape-runs/hooks/use-scrape-progress.ts` - Changed from /api/scrape/stream to /api/scrape/runs/{id}/progress
- `src/market_mapping/types/sportybet.py` - Made far_near_odds, root_market_id, node_market_id optional

## Decisions Made

- UAT-001 platform status icons: No code fix needed. The `getPlatformStatuses()` logic was correct; the issue was caused by UAT-002's cascade scrapes corrupting `platform_timings` data in the database.
- Use observe pattern: The key insight is `/api/scrape/stream` creates AND starts a new scrape (used by dashboard "Start New Scrape" button), while `/api/scrape/runs/{id}/progress` observes an existing scrape (used by detail page).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all fixes applied cleanly.

## Next Phase Readiness

- All Phase 14 UAT issues resolved
- Scraping workflow now stable with proper logging and state tracking
- Ready for milestone completion or next phase work

---
*Phase: 14-scraping-logging-workflow*
*Completed: 2026-01-22*
