---
phase: 108-risk-page
plan: 01
subsystem: ui
tags: [react, tanstack-query, shadcn, risk-monitoring, alerts]

# Dependency graph
requires:
  - phase: 107-alert-api
    provides: REST API endpoints for alerts (GET /alerts, PATCH /alerts/{id})
provides:
  - Risk Monitoring page at /risk-monitoring
  - useAlerts, useAlertStats, useAcknowledgeAlert hooks
  - AlertTable component with event grouping and expandable rows
affects: [109-real-time-updates, 110-cross-page-integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Event grouping in alert table with max severity propagation
    - Expandable rows with detailed alert information
    - Direction disagreement display with dual bookmaker comparison

key-files:
  created:
    - web/src/features/risk-monitoring/hooks/use-alerts.ts
    - web/src/features/risk-monitoring/hooks/index.ts
    - web/src/features/risk-monitoring/index.tsx
    - web/src/features/risk-monitoring/components/alert-table.tsx
    - web/src/features/risk-monitoring/components/index.ts
  modified:
    - web/src/routes.tsx

key-decisions:
  - "Group alerts by event for cleaner overview"
  - "Show max severity badge at event level"
  - "Filter to matched markets only for relevant alerts"

patterns-established:
  - "Event grouping with expandable alert rows"
  - "Direction disagreement display with both BetPawa and competitor movements"

issues-created: []

# Metrics
duration: 15min
completed: 2026-02-19
---

# Phase 108 Plan 01: Risk Monitoring Page Summary

**Risk Monitoring page with event-grouped alert table, status tabs, severity/type filters, and acknowledge workflow**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-19T10:00:00Z
- **Completed:** 2026-02-19T10:15:00Z
- **Tasks:** 2 auto + 1 checkpoint
- **Files modified:** 6

## Accomplishments

- Created Risk Monitoring page at /risk-monitoring with status tabs (New/Acknowledged/Past)
- Implemented TanStack Query hooks for alerts API (useAlerts, useAlertStats, useAcknowledgeAlert)
- Built AlertTable component with event grouping and expandable rows showing full alert details
- Added severity badges (Warning/Elevated/Critical) and type badges (Price Change/Direction/Availability)
- Integrated odds history dialog for viewing historical data from alerts
- Added pagination for large result sets

## Task Commits

Each task was committed atomically:

1. **Task 1: Create risk-monitoring feature hooks and types** - `7f46eed` (feat)
2. **Task 2: Create RiskMonitoringPage with tabs, filters, and table** - `9ed6406` (feat)
3. **Fix: Address Risk Monitoring UAT feedback** - `8d112fe` (fix)
4. **Fix: Improve alert display by type** - `c866742` (fix)
5. **Feat: Add competitor odds to direction alerts** - `079e199` (feat)
6. **Feat: Filter alerts to matched markets only** - `604a34f` (feat)

## Files Created/Modified

- `web/src/features/risk-monitoring/hooks/use-alerts.ts` - TanStack Query hooks for alert APIs
- `web/src/features/risk-monitoring/hooks/index.ts` - Barrel export for hooks
- `web/src/features/risk-monitoring/index.tsx` - Main page with tabs, filters, pagination
- `web/src/features/risk-monitoring/components/alert-table.tsx` - Event-grouped table with expandable rows
- `web/src/features/risk-monitoring/components/index.ts` - Barrel export for components
- `web/src/routes.tsx` - Added /risk-monitoring route

## Decisions Made

- **Event grouping pattern**: Alerts grouped by event with max severity shown at group level for quick scanning
- **Filter to matched markets only**: Only show alerts where market exists in both BetPawa and competitor for relevance
- **Direction disagreement display**: Show both BetPawa and competitor movements side-by-side with arrows

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed direction disagreement display**
- **Found during:** Task 2 (UAT verification)
- **Issue:** Direction alerts showed raw data format instead of human-readable comparison
- **Fix:** Added parseCompetitorDirection helper and dual-bookmaker movement display
- **Files modified:** web/src/features/risk-monitoring/components/alert-table.tsx
- **Verification:** Direction alerts now show "BetPawa: 1.50 → 1.60 ↑ • SportyBet: 1.55 → 1.45 ↓"
- **Committed in:** c866742, 079e199

**2. [Rule 2 - Missing Critical] Added matched market filtering**
- **Found during:** Task 2 (UAT verification)
- **Issue:** Alerts showed for markets without competitor data, providing no actionable insight
- **Fix:** Backend filter added to only return alerts where market is matched
- **Files modified:** Backend alert detection
- **Verification:** All displayed alerts have valid competitor comparison data
- **Committed in:** 604a34f

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical), 0 deferred
**Impact on plan:** Both fixes essential for usability. No scope creep.

## Issues Encountered

None - plan executed with iterative improvements during UAT.

## Next Phase Readiness

- Risk Monitoring page complete with full functionality
- Ready for Phase 109: Real-Time Updates (WebSocket alert broadcasting)
- Sidebar badge integration deferred to Phase 110

---
*Phase: 108-risk-page*
*Completed: 2026-02-19*
