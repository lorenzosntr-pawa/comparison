---
phase: 69-investigation-freshness-audit
plan: 01
subsystem: observability
tags: [timestamp, cache, websocket, freshness, audit]

# Dependency graph
requires:
  - phase: 55-async-write-pipeline
    provides: change detection and last_confirmed_at field
  - phase: 57-websocket-infrastructure
    provides: WebSocket odds_update broadcasting
  - phase: 63-freshness-timestamps
    provides: snapshot_time field in API
provides:
  - Complete data flow documentation from scrape to display
  - 7 staleness sources identified and prioritized (2 CRITICAL, 2 HIGH, 2 MEDIUM, 1 LOW)
  - Fix recommendations mapped to Phase 70 (backend) and Phase 71 (frontend)
  - Verification checklist for freshness testing
affects: [70-backend-freshness-fixes, 71-frontend-freshness-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/69-investigation-freshness-audit/FRESHNESS-AUDIT.md
  modified: []

key-decisions:
  - "Root cause identified: API uses captured_at (time of change) instead of last_confirmed_at (time of last scrape)"
  - "Frontend odds_updates subscription missing - WebSocket infrastructure exists but unused"

patterns-established:
  - "Investigation-first approach: audit before implementation"
  - "Timestamp lifecycle documentation for complex data flows"

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-09
---

# Phase 69 Plan 01: Investigation & Freshness Audit Summary

**Identified root cause: API uses `captured_at` (time odds changed) instead of `last_confirmed_at` (time last scraped), plus frontend missing WebSocket odds_updates subscription**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-09T10:00:00Z
- **Completed:** 2026-02-09T10:12:00Z
- **Tasks:** 3
- **Files modified:** 1 created (FRESHNESS-AUDIT.md)

## Accomplishments

- Traced complete data flow from scraping through cache to API to frontend
- Documented timestamp lifecycle: `captured_at` vs `last_confirmed_at` discrepancy
- Identified 7 staleness sources across backend and frontend (2 CRITICAL, 2 HIGH, 2 MEDIUM, 1 LOW)
- Created comprehensive FRESHNESS-AUDIT.md with data flow diagrams and fix recommendations
- Verified WebSocket infrastructure exists but frontend doesn't subscribe to odds_updates topic

## Task Commits

This was a pure investigation phase - no code changes:

1. **Task 1: Trace backend data flow** - (investigation)
2. **Task 2: Trace WebSocket and frontend path** - (investigation)
3. **Task 3: Compile audit report** - (investigation)

**Plan metadata:** See commit (docs: complete investigation plan)

## Files Created/Modified

- `.planning/phases/69-investigation-freshness-audit/FRESHNESS-AUDIT.md` - Complete audit document (239 lines)

## Decisions Made

1. **Root cause is timestamp field choice**: API returns `captured_at` (when odds changed) but should return `last_confirmed_at` (when odds were last verified)
2. **Fix should use existing field**: `last_confirmed_at` already exists and is updated every scrape - just need to expose it in API

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - investigation completed successfully.

## Key Findings

### CRITICAL Issues

1. **Cache/DB Timestamp Inconsistency**: Cache stores `captured_at = now_naive` (fresh), but DB uses `server_default` (only on INSERT). After restart/cache miss, timestamps appear stale.

2. **API Uses Wrong Field**: `events.py` returns `snapshot_time = snapshot.captured_at` instead of `last_confirmed_at`. The fix field exists but isn't exposed.

### HIGH Issues

3. **Frontend Missing odds_updates Subscription**: Only subscribes to `['scrape_progress']`, not `['odds_updates']`. WebSocket broadcasts but frontend ignores.

4. **No Query Invalidation on odds_update**: Even if subscribed, no handler exists to refresh data on individual odds changes.

## Next Phase Readiness

Phase 70 (Backend Freshness Fixes) should address:
- Change `events.py` to use `last_confirmed_at` for `snapshot_time`
- Optionally add `last_confirmed_at` to CachedSnapshot
- Ensure cache warmup loads correct timestamp field

Phase 71 (Frontend Freshness Fixes) should address:
- Subscribe to `odds_updates` WebSocket topic
- Add handler to invalidate affected event queries
- Consider reducing poll interval when WebSocket connected

---
*Phase: 69-investigation-freshness-audit*
*Completed: 2026-02-09*
