---
phase: 11-settings-page
plan: 11-FIX
type: fix
---

<objective>
Fix 1 UAT issue from Phase 11 Settings Page testing.

Source: 11-ISSUES.md
Priority: 1 blocker

**Issue:** Scheduler pause/resume UI doesn't reflect actual state. The backend's paused detection logic is incorrect - it checks if all jobs have `next_run_time = None` instead of checking APScheduler's actual paused state.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/11-settings-page/11-ISSUES.md

**Original plan for reference:**
@.planning/phases/11-settings-page/11-01-PLAN.md
@.planning/phases/11-settings-page/11-02-PLAN.md

**Relevant code files:**
@src/api/routes/scheduler.py (line 54 has incorrect paused detection)
@src/scheduling/scheduler.py (scheduler instance)
</context>

<tasks>
<task type="auto">
  <name>Task 1: Fix scheduler paused state detection in backend</name>
  <files>src/api/routes/scheduler.py</files>
  <action>
Fix the paused detection logic in `get_scheduler_status()` endpoint.

**Current incorrect logic (line 54):**
```python
paused = scheduler.running and all(job.next_run_time is None for job in scheduler.get_jobs())
```

**Problem:** APScheduler's `scheduler.pause()` doesn't set job `next_run_time` to None. It sets an internal state flag. The scheduler has three states:
- `STATE_STOPPED = 0`
- `STATE_RUNNING = 1`
- `STATE_PAUSED = 2`

**Fix:** Import the state constants and check the scheduler's actual state:

```python
from apscheduler.schedulers.base import STATE_PAUSED

# In get_scheduler_status():
paused = scheduler.state == STATE_PAUSED
```

This correctly detects when `scheduler.pause()` has been called.
  </action>
  <verify>
1. Start the backend server
2. Call GET /api/scheduler/status - should show `paused: false`
3. Call POST /api/scheduler/pause - should return success
4. Call GET /api/scheduler/status - should now show `paused: true`
5. Call POST /api/scheduler/resume - should return success
6. Call GET /api/scheduler/status - should show `paused: false` again
  </verify>
  <done>
- GET /api/scheduler/status correctly returns `paused: true` after pause and `paused: false` after resume
- UI button state changes correctly after pause/resume
- Dashboard reflects correct scheduler state
  </done>
</task>
</tasks>

<verification>
Before declaring plan complete:
- [ ] Backend correctly reports paused state via GET /api/scheduler/status
- [ ] Settings page shows "Resume" button after pausing
- [ ] Dashboard widget shows "Paused" status after pausing
- [ ] Resume functionality restores "Running" status everywhere
</verification>

<success_criteria>
- UAT-001 from 11-ISSUES.md addressed
- Pause/resume UI reflects actual scheduler state
- Ready for re-verification
</success_criteria>

<output>
After completion, create `.planning/phases/11-settings-page/11-FIX-SUMMARY.md`
</output>
