---
phase: 14-scraping-logging-workflow
plan: 02-FIX2
subsystem: scraping, api
tags: [sse, background-task, sportradar-ids, uat-fix]

# Dependency graph
requires:
  - phase: 14-02-FIX
    provides: Platform enum with BetPawa-first ordering
provides:
  - Decoupled scrape execution from SSE connection lifecycle
  - Fresh SportRadar ID passing between platforms
affects: [scraping-workflow, api-endpoints, event-matching]

# Tech tracking
tech-stack:
  added: []
  patterns: [asyncio background tasks, pub/sub broadcasting, session-scoped ID propagation]

key-files:
  created: []
  modified:
    - src/api/routes/scrape.py
    - src/scraping/orchestrator.py

key-decisions:
  - "Spawn scrape as asyncio background task with its own DB session"
  - "Use progress_registry broadcaster for pub/sub SSE updates"
  - "Pass fresh SportRadar IDs from BetPawa to competitor platforms"
  - "Bet9ja filters results to match BetPawa session IDs"
  - "SportyBet uses provided IDs directly (no DB query)"

patterns-established:
  - "Background tasks with independent DB sessions for request-independent operations"
  - "Session-scoped ID propagation for cross-platform data consistency"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-22
---

# Phase 14-02-FIX2: UAT Issue Fixes Summary

**Decouple scrape from SSE lifecycle and pass fresh SportRadar IDs between platforms**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-22T02:00:00Z
- **Completed:** 2026-01-22T02:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

### Task 1: Fix UAT-003 - Decouple scrape execution from SSE connection lifecycle (Blocker)
- Modified `stream_scrape()` to spawn scrape as `asyncio.create_task()` background task
- Background task uses its own DB session via `async_session_factory`
- SSE endpoint subscribes to `progress_registry` broadcaster
- Scrape continues running even when client disconnects
- Added imports: `asyncio`, `ScrapeProgress`, `async_session_factory`

### Task 2: Fix UAT-004 - Pass fresh SportRadar IDs from BetPawa to SportyBet/Bet9ja (Major)
- Collect SportRadar IDs during BetPawa scrape in `scrape_with_progress()`
- Pass IDs to `_scrape_platform()` via new `sportradar_ids` parameter
- Updated `_scrape_sportybet()` to use provided IDs directly (no DB query needed)
- Updated `_scrape_bet9ja()` to filter results to matching SportRadar IDs
- Updated `_store_events()` for SportyBet to handle cases where event not yet in DB

## Task Commits

Each task was committed atomically:

1. **Task 1: Decouple scrape execution from SSE connection lifecycle** - `07ce8fa` (fix)
2. **Task 2: Pass fresh SportRadar IDs from BetPawa to SportyBet/Bet9ja** - `766a325` (fix)

**Plan metadata:** `64897da` (docs)

## Files Created/Modified
- `src/api/routes/scrape.py` - Background task pattern for scrape execution
- `src/scraping/orchestrator.py` - SportRadar ID collection and propagation

## Technical Details

### Background Task Pattern (Task 1)
```python
async def run_scrape_background():
    async with async_session_factory() as bg_db:
        # Scrape with independent DB session
        async for progress in orchestrator.scrape_with_progress(..., db=bg_db):
            await broadcaster.publish(progress)

asyncio.create_task(run_scrape_background())  # Fire-and-forget
```

### SportRadar ID Flow (Task 2)
1. BetPawa scrapes first (enum order)
2. Collect SportRadar IDs: `[e["sportradar_id"] for e in events]`
3. Pass to SportyBet: Uses IDs directly without DB query
4. Pass to Bet9ja: Filters tournament results to matching IDs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness
- UAT-003 (Blocker) and UAT-004 (Major) from 14-02-ISSUES.md are now fixed
- Ready for re-verification with /gsd:verify-work 14-02
- Scrape execution survives SSE client disconnects
- SportyBet/Bet9ja use fresh IDs from current BetPawa session

---
*Phase: 14-scraping-logging-workflow*
*Completed: 2026-01-22*
