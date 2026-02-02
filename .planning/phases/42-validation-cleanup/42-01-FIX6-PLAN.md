---
phase: 42-validation-cleanup
plan: FIX6
type: fix
---

<objective>
Fix 2 UAT issues from plan 42-01-FIX5: missing betpawa_event_id linking in EventCoordinator.

Source: 42-01-FIX5-ISSUES.md
Priority: 2 blockers (both critical for data display)

Root cause: `_create_competitor_event_from_raw()` never sets `betpawa_event_id`, breaking coverage stats and cross-platform matching.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/42-validation-cleanup/42-01-FIX5-ISSUES.md

**Key source files:**
@src/scraping/event_coordinator.py
@src/scraping/competitor_events.py (reference for correct pattern)
@src/api/routes/palimpsest.py (coverage API)
@src/api/routes/events.py (events API)
</context>

<tasks>
<task type="auto">
  <name>Task 1: Add betpawa_event_id lookup to _create_competitor_event_from_raw</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
In `_create_competitor_event_from_raw()` method (around line 1668):

1. Before creating the CompetitorEvent, look up the BetPawa Event by SR ID:
```python
# Look up BetPawa event by sportradar_id (same as competitor_events.py pattern)
bp_event_result = await db.execute(
    select(Event.id).where(Event.sportradar_id == sr_id)
)
betpawa_event_id = bp_event_result.scalar_one_or_none()
```

2. Add `betpawa_event_id=betpawa_event_id` to the CompetitorEvent constructor.

This matches the pattern from competitor_events.py:119-136 that worked correctly in v1.6.

Import Event model at top of file if not already imported.
  </action>
  <verify>Code compiles without errors, Event import present</verify>
  <done>CompetitorEvent created with betpawa_event_id populated when BetPawa Event exists</done>
</task>

<task type="auto">
  <name>Task 2: Add post-batch reconciliation for ordering edge cases</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
In `store_batch_results()` method, after the main processing loop but BEFORE the commit:

Add a reconciliation pass to link any CompetitorEvents that were created before their BetPawa Event in the same batch:

```python
# Reconciliation pass: Link CompetitorEvents created before their BetPawa Event in this batch
# This handles ordering edge case where competitor processed before BetPawa in same batch
for sr_id, event_id in event_id_map.items():
    # Update any CompetitorEvents for this SR ID that have NULL betpawa_event_id
    await db.execute(
        update(CompetitorEvent)
        .where(
            CompetitorEvent.sportradar_id == sr_id,
            CompetitorEvent.betpawa_event_id.is_(None)
        )
        .values(betpawa_event_id=event_id)
    )
```

Place this after the competitor_snapshots loop (around line 1168) and before the bulk insert section (line 1181).

Import `update` from sqlalchemy if not already imported.
  </action>
  <verify>Code compiles without errors</verify>
  <done>Reconciliation pass updates CompetitorEvents with betpawa_event_id after batch processing</done>
</task>

<task type="auto">
  <name>Task 3: Test with fresh scrape</name>
  <files>None (testing)</files>
  <action>
1. Clear stale data (if database has old data without betpawa_event_id):
```sql
-- Optional: Clear only if needed for clean test
DELETE FROM competitor_odds_snapshots;
DELETE FROM odds_snapshots;
DELETE FROM event_scrape_status;
DELETE FROM competitor_events;
DELETE FROM events;
```

2. Start the backend: `python -m uvicorn "src.api.app:create_app" --factory --reload --port 8000`

3. Trigger a scrape via UI or wait for scheduled scrape

4. Check logs for successful batch storage

5. Verify in logs or via SQL:
```sql
-- Count CompetitorEvents with betpawa_event_id set
SELECT COUNT(*) as linked,
       COUNT(*) FILTER (WHERE betpawa_event_id IS NOT NULL) as matched
FROM competitor_events;
```

Expected: Most CompetitorEvents should have betpawa_event_id set (those with matching BetPawa events).
  </action>
  <verify>Logs show batch storage complete; SQL query shows matched count > 0</verify>
  <done>CompetitorEvents are being linked to BetPawa Events via betpawa_event_id</done>
</task>
</tasks>

<verification>
Before declaring plan complete:
- [ ] Code compiles without TypeScript/Python errors
- [ ] Backend starts without import errors
- [ ] Fresh scrape completes successfully
- [ ] CompetitorEvents have betpawa_event_id populated
- [ ] Ready for UAT re-test of coverage and odds pages
</verification>

<success_criteria>
- UAT-001 root cause addressed: betpawa_event_id now set on CompetitorEvents
- UAT-002 root cause addressed: same fix enables cross-platform odds display
- Backend storage correctly links competitor events to BetPawa events
- Ready for user acceptance testing
</success_criteria>

<output>
After completion, create `.planning/phases/42-validation-cleanup/42-01-FIX6-SUMMARY.md`
</output>
