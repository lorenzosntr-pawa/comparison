---
phase: 22-history-retention
plan: 22-FIX
type: fix
---

<objective>
Fix 1 UAT blocker issue from Phase 22 user acceptance testing.

Source: 22-ISSUES.md
Priority: 1 blocker, 0 major, 0 minor

Purpose: Apply missing database migration so Phase 22 features can be tested.
Output: Working backend with retention settings columns in database.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/22-history-retention/22-ISSUES.md

**Original plan for reference:**
@.planning/phases/22-history-retention/22-01-PLAN.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Apply Alembic migrations</name>
  <files>Database schema (no code files modified)</files>
  <action>
Run Alembic to apply all pending migrations:

```bash
alembic upgrade head
```

This will apply:
- b8c4d2e5f9g3_update_retention_settings.py (from 22-01: renames history_retention_days → odds_retention_days, adds match_retention_days, cleanup_frequency_hours)
- c9d5e3f6g7h8_add_cleanup_runs.py (from 22-02: adds cleanup_runs table)

After migration, verify the columns exist.
  </action>
  <verify>
Run: `alembic current` - should show latest migration as current
Run: Database query to verify columns exist:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name = 'settings';
```
Should include: odds_retention_days, match_retention_days, cleanup_frequency_hours
  </verify>
  <done>All migrations applied, settings table has new retention columns</done>
</task>

<task type="auto">
  <name>Task 2: Verify backend starts without errors</name>
  <files>None (verification only)</files>
  <action>
Start the backend server and verify it can:
1. Start without database errors
2. Respond to /api/settings endpoint
3. Return settings with new retention fields

Test command:
```bash
curl http://localhost:8000/api/settings
```
  </action>
  <verify>
- Backend starts without errors
- GET /api/settings returns 200 with oddsRetentionDays, matchRetentionDays, cleanupFrequencyHours fields
  </verify>
  <done>Backend operational, settings API working with new retention fields</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] `alembic current` shows latest migration
- [ ] Settings table has all three new columns
- [ ] Backend starts without database errors
- [ ] /api/settings endpoint returns new retention fields
</verification>

<success_criteria>
- UAT-001 resolved: Database migration applied
- Backend fully operational
- Ready for re-verification of Phase 22 features
</success_criteria>

<output>
After completion, create `.planning/phases/22-history-retention/22-FIX-SUMMARY.md`
Update 22-ISSUES.md to move UAT-001 to Resolved section.
</output>
