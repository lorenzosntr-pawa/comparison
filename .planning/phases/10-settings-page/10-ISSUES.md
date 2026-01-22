# UAT Issues: Phase 11 Settings Page

**Tested:** 2026-01-22
**Source:** .planning/phases/11-settings-page/11-01-SUMMARY.md, 11-02-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Scheduler pause/resume UI doesn't reflect actual state

**Discovered:** 2026-01-22
**Resolved:** 2026-01-22 - Fixed in 11-FIX.md
**Commit:** a2e4434
**Phase/Plan:** 11-01, 11-02
**Severity:** Blocker
**Feature:** Scheduler Control
**Description:** When clicking Pause, the API returns success (`{"success":true,"paused":true,"message":"Scheduler paused successfully"}`) but the UI doesn't update. The button still shows "Pause" instead of changing to "Resume". Additionally, the dashboard still shows the scheduler as active.
**Root Cause:** Backend used incorrect logic to detect paused state - checked if all jobs had `next_run_time = None` instead of using APScheduler's `STATE_PAUSED` state constant.
**Fix:**
1. Backend: Import `STATE_PAUSED` from `apscheduler.schedulers.base` and check `scheduler.state == STATE_PAUSED`
2. Dashboard: Add 'paused' status to StatusCard component and update logic to show paused state
3. Hooks: Use `refetchQueries` instead of `invalidateQueries` for immediate sync

---

*Phase: 11-settings-page*
*Tested: 2026-01-22*
