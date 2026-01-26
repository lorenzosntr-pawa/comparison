# UAT Issues: Phase 22

**Tested:** 2026-01-25
**Source:** .planning/phases/22-history-retention/22-01-SUMMARY.md through 22-03-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Database migration not applied - settings columns missing

**Discovered:** 2026-01-25
**Resolved:** 2026-01-25 - Fixed in 22-FIX.md
**Phase/Plan:** 22-01
**Severity:** Blocker
**Feature:** Retention settings model
**Description:** Backend throws error on startup: `column settings.odds_retention_days does not exist`. The Alembic migration from 22-01 has not been applied to the database.
**Resolution:** Ran `alembic upgrade head` which applied:
- b8c4d2e5f9g3_update_retention_settings.py (adds retention columns)
- c9d5e3f6g7h8_add_cleanup_runs.py (adds cleanup_runs table)
**Verification:**
- `alembic current` shows c9d5e3f6g7h8 (head)
- GET /api/settings returns 200 with oddsRetentionDays, matchRetentionDays, cleanupFrequencyHours
- GET /api/cleanup/stats returns 200 with data statistics

---

*Phase: 22-history-retention*
*Tested: 2026-01-25*
