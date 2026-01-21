---
phase: 08-scrape-runs-ui-improvements
plan: 03
subsystem: ui, api
tags: [fastapi, react, shadcn, tanstack-query, retry]

# Dependency graph
requires:
  - phase: 08-02
    provides: Scrape runs detail page with errors list and platform breakdown
provides:
  - POST /api/scrape/{run_id}/retry endpoint with platform selection
  - RetryDialog component with platform checkboxes
  - useRetry mutation hook for retry operations
  - Retry button on detail page for partial/failed runs
affects: [phase-9, phase-10]

# Tech tracking
tech-stack:
  added: [radix-ui/react-dialog]
  patterns: [Platform-specific retry with trigger audit trail]

key-files:
  created:
    - web/src/features/scrape-runs/hooks/use-retry.ts
    - web/src/features/scrape-runs/components/retry-dialog.tsx
    - web/src/components/ui/dialog.tsx
  modified:
    - src/api/routes/scrape.py
    - src/api/schemas/scheduler.py
    - src/api/schemas/__init__.py
    - web/src/features/scrape-runs/detail.tsx
    - web/src/features/scrape-runs/hooks/index.ts
    - web/src/features/scrape-runs/components/index.ts

key-decisions:
  - "Create new ScrapeRun for retry (audit trail) instead of modifying original"
  - "Use trigger='retry:{original_id}' to link retry runs to originals"
  - "Determine failed platforms from errors + missing platform_timings"

patterns-established:
  - "Retry endpoint creates new run with linked trigger field"
  - "Platform selection dialog with pre-checked failed platforms"
  - "Navigate to new run detail page on successful retry"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-21
---

# Phase 08: Platform-Specific Retry Summary

**Retry API endpoint and dialog component for retrying failed platforms with new ScrapeRun audit trail**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-21T13:00:00Z
- **Completed:** 2026-01-21T13:08:00Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- POST /api/scrape/{run_id}/retry endpoint accepting platform list
- Validates run status (can't retry running scrape)
- Creates new ScrapeRun with trigger="retry:{original_id}" for audit trail
- RetryDialog component with platform checkboxes and error count badges
- useRetry mutation hook with query invalidation
- "Retry Failed" button on detail page header for partial/failed runs
- Automatic failed platform detection from errors and missing timings

## Task Commits

Each task was committed atomically:

1. **Task 1: Add retry endpoint with platform selection** - `646ede4` (feat)
2. **Task 2: Create retry dialog component** - `881cbd4` (feat)
3. **Task 3: Integrate retry button on detail page** - `027afd2` (feat)

**Plan metadata:** [pending commit]

## Files Created/Modified
- `src/api/schemas/scheduler.py` - Added RetryRequest, RetryResponse schemas
- `src/api/schemas/__init__.py` - Export retry schemas
- `src/api/routes/scrape.py` - Added POST /api/scrape/{run_id}/retry endpoint
- `web/src/components/ui/dialog.tsx` - shadcn Dialog component (installed)
- `web/src/features/scrape-runs/hooks/use-retry.ts` - Retry mutation hook
- `web/src/features/scrape-runs/hooks/index.ts` - Export useRetry hook
- `web/src/features/scrape-runs/components/retry-dialog.tsx` - Retry dialog with platform selection
- `web/src/features/scrape-runs/components/index.ts` - Export RetryDialog
- `web/src/features/scrape-runs/detail.tsx` - Added retry button and dialog integration

## Decisions Made
- New ScrapeRun created for each retry (preserves original for audit trail)
- Trigger field stores "retry:{original_id}" for traceability
- Failed platforms determined from: 1) platforms in errors, 2) platforms missing from successful timings
- All failed platforms pre-selected in dialog by default

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered

None

## Next Phase Readiness
- Phase 8 complete - all 3 plans finished
- Retry functionality enables targeted recovery from partial failures
- Ready for Phase 9: Market Mapping Expansion

---
*Phase: 08-scrape-runs-ui-improvements*
*Completed: 2026-01-21*
