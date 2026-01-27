---
phase: 32-connection-loss-logging
plan: "01"
subsystem: infra
tags: [sse, connection-detection, structlog, auto-recovery]

requires:
  - phase: 31-backend-heartbeat
    provides: stale run detection infrastructure
provides:
  - CONNECTION_FAILED status enum and disconnect detection
  - Auto-rescrape on frontend recovery from connection loss
affects: [33-detailed-progress, 34-inline-errors]

tech-stack:
  added: []
  patterns:
    - "SSE subscriber count monitoring for disconnect detection"
    - "Auto-rescrape with useRef loop guard on page reload"

key-files:
  created: []
  modified:
    - src/db/models/scrape.py
    - src/scraping/broadcaster.py
    - src/api/routes/scrape.py
    - web/src/features/dashboard/components/recent-runs.tsx
    - web/src/features/scrape-runs/components/runs-table.tsx
    - web/src/features/scrape-runs/detail.tsx

key-decisions:
  - "Auto-rescrape implemented in recent-runs.tsx (scrape-control.tsx doesn't exist)"

patterns-established:
  - "formatStatus helper for human-readable status labels"
  - "Subscriber count check between platform completions for disconnect detection"

issues-created: []

duration: 4min
completed: 2026-01-27
---

# Phase 32 Plan 01: Connection Loss Logging Summary

**SSE disconnect detection via subscriber count monitoring, CONNECTION_FAILED status with destructive badge, and auto-rescrape on page reload recovery**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-27T16:16:30Z
- **Completed:** 2026-01-27T16:20:52Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- CONNECTION_FAILED status added to ScrapeStatus enum (no migration needed — VARCHAR storage)
- Backend detects zero SSE subscribers between platform completions and marks run as connection_failed with structlog warning
- Frontend displays "Connection Lost" with red destructive badge in all run views
- Auto-rescrape triggers once on page reload when latest run is connection_failed

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CONNECTION_FAILED status and backend disconnect detection** - `8777245` (feat)
2. **Task 2: Frontend disconnect handling, status display, and auto-rescrape** - `45bb93f` (feat)

## Files Created/Modified
- `src/db/models/scrape.py` - Added CONNECTION_FAILED enum value
- `src/scraping/broadcaster.py` - Added subscriber_count property
- `src/api/routes/scrape.py` - Disconnect detection in run_scrape_background()
- `web/src/features/dashboard/components/recent-runs.tsx` - Status variant, formatStatus, auto-rescrape logic
- `web/src/features/scrape-runs/components/runs-table.tsx` - Status variant and formatStatus
- `web/src/features/scrape-runs/detail.tsx` - Status variant, formatStatus, canRetry for connection_failed

## Decisions Made
- Auto-rescrape implemented in recent-runs.tsx rather than scrape-control.tsx (which doesn't exist) — the scrape trigger already lives in recent-runs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] scrape-control.tsx doesn't exist**
- **Found during:** Task 2 (auto-rescrape implementation)
- **Issue:** Plan referenced scrape-control.tsx but scrape trigger logic lives in recent-runs.tsx
- **Fix:** Implemented auto-rescrape in recent-runs.tsx where startScrape already exists
- **Files modified:** web/src/features/dashboard/components/recent-runs.tsx
- **Verification:** Auto-rescrape logic present with useRef guard
- **Committed in:** 45bb93f

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor file location change. No scope creep.

## Issues Encountered
None

## Next Phase Readiness
- CONNECTION_FAILED status fully integrated backend and frontend
- Ready for Phase 33 (Detailed Per-Platform Progress Messages)

---
*Phase: 32-connection-loss-logging*
*Completed: 2026-01-27*
