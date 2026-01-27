---
phase: 31-backend-heartbeat
plan: "01"
title: Backend Heartbeat & Stale Run Detection
status: complete
started: 2026-01-27
completed: 2026-01-27
duration: ~5 min
tasks_completed: 2
tasks_total: 2
files_created: 1
files_modified: 2
---

# 31-01 Summary: Backend Heartbeat & Stale Run Detection

## Accomplishments

1. **Stale run detection module** — Created `src/scheduling/stale_detection.py` with four functions:
   - `find_stale_runs()` queries RUNNING runs using MAX(ScrapePhaseLog.started_at) subquery with fallback to ScrapeRun.started_at
   - `mark_run_stale()` sets FAILED status with ScrapeError (error_type="stale") and optimistic concurrency check
   - `detect_stale_runs()` async watchdog job with broadcaster cleanup and single commit
   - `recover_stale_runs_on_startup()` fails all RUNNING runs at startup before scheduler begins

2. **Watchdog job registration** — Added detect_stale_runs to configure_scheduler() with IntervalTrigger(minutes=2), coalesce=True, misfire_grace_time=60

3. **Startup recovery** — Called recover_stale_runs_on_startup() in app lifespan BEFORE configure_scheduler() to ensure clean state

## Files

### Created
- `src/scheduling/stale_detection.py` — Stale detection module (4 functions, ~160 lines)

### Modified
- `src/scheduling/scheduler.py` — Added detect_stale_runs import and job registration
- `src/api/app.py` — Added startup recovery call before scheduler init

## Decisions

- Used optimistic concurrency: re-check run.status before marking stale to avoid race with orchestrator
- No broadcaster cleanup needed at startup (ProgressRegistry is in-memory, empty after restart)
- Single commit per detect_stale_runs() invocation for efficiency
- 10-minute default threshold for staleness detection

## Deviations

None.

## Task Commits

| Task | Commit | Hash |
|------|--------|------|
| Task 1: Create stale detection module and register watchdog job | `feat(31-01): create stale run detection module and register watchdog job` | `fa22b64` |
| Task 2: Add startup recovery for stale runs | `feat(31-01): add startup recovery for stale runs` | `bc54290` |
