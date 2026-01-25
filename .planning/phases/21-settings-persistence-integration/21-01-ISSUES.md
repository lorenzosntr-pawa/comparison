# UAT Issues: Phase 21 Plan 01

**Tested:** 2026-01-25
**Source:** .planning/phases/21-settings-persistence-integration/21-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Database column history_retention_days does not exist

**Discovered:** 2026-01-25
**Phase/Plan:** 21-01
**Severity:** Blocker
**Feature:** Settings persistence at startup
**Description:** On server startup, the sync_settings_on_startup() function fails to fetch settings because the database column `history_retention_days` does not exist. The SQLAlchemy model expects this column but the database schema doesn't have it.
**Expected:** Server starts and successfully loads settings from database, including history_retention_days field
**Actual:** Error on startup: `column settings.history_retention_days does not exist` - SQLAlchemy query fails with UndefinedColumnError
**Repro:**
1. Start the backend server with `python -m uvicorn "src.api.app:create_app" --factory --reload --port 8000`
2. Observe error in console: `Failed to fetch settings from database`
**Root cause:** Phase 20 added history_retention_days to the SQLAlchemy model but the database migration to add the column was not applied (or not created)

**Resolved:** 2026-01-25 - Fixed in 21-01-FIX.md
**Fix:** Applied pending Alembic migration `a7b3c1d4e8f2_add_history_retention_setting.py` via `alembic upgrade head`. Also corrected alembic.ini database URL from `5432/betpawa` to `5433/pawarisk`.

---

*Phase: 21-settings-persistence-integration*
*Plan: 01*
*Tested: 2026-01-25*
