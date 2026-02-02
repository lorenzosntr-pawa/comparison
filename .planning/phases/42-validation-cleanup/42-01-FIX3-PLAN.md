---
phase: 42-validation-cleanup
plan: 01-FIX3
type: fix
---

<objective>
Fix UAT-001: BetPawa event discovery still returns 0 events.

Source: 42-01-FIX2-ISSUES.md
Priority: 1 blocker

Root cause analysis from old working code (git show 25eda49^:src/scraping/orchestrator.py):

1. **SR ID extraction path is wrong**:
   - Old working code: `widget.get("id")`
   - New broken code: `widget.get("data", {}).get("matchId", "")`

2. **Old code parsed events from list response WITH widgets**:
   The old `_parse_betpawa_event` expected widgets IN the list response and extracted SR ID directly. If list response has widgets, the new code's approach of fetching full event is unnecessary.

3. **If list has no widgets, old code would fail too**:
   Need to verify which is correct by checking actual response.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md

**Issues being fixed:**
@.planning/phases/42-validation-cleanup/42-01-FIX2-ISSUES.md

**Original implementation:**
@src/scraping/event_coordinator.py

**Old working code (reference):**
git show 25eda49^:src/scraping/orchestrator.py

Key patterns from old code:
- `_parse_betpawa_event`: extracts SR ID via `widget.get("id")` not `widget.data.matchId`
- Expected fields in list response: id, startTime, widgets[], participants[]
</context>

<tasks>

<task type="auto">
  <name>Task 1: Port old working _parse_betpawa_event logic</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
Replace the inline event parsing in `_discover_betpawa()` with logic from the old working `_parse_betpawa_event`.

The old code (from git show 25eda49^:src/scraping/orchestrator.py):
```python
def _parse_betpawa_event(self, data: dict) -> dict | None:
    # Extract SportRadar ID from widgets
    widgets = data.get("widgets", [])
    sportradar_id = None
    for widget in widgets:
        if widget.get("type") == "SPORTRADAR":
            sportradar_id = widget.get("id")  # <-- KEY: uses widget["id"], NOT widget["data"]["matchId"]
            break

    if not sportradar_id:
        return None

    # Parse kickoff
    start_time_str = data.get("startTime", "")
    kickoff = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))

    event_id = str(data.get("id", ""))
    # ... return parsed dict
```

Changes to make in `_discover_betpawa()`:

1. In the events parsing loop (around line 293), try to get SR ID directly from list response widgets FIRST using `widget.get("id")`:
   ```python
   for event_data in events_data:
       # Try to get SR ID from list response (old pattern)
       widgets = event_data.get("widgets", [])
       sr_id = None
       for widget in widgets:
           if widget.get("type") == "SPORTRADAR":
               sr_id = widget.get("id")  # Use "id" not "data.matchId"
               break

       event_id = str(event_data.get("id", ""))
       start_time = event_data.get("startTime")

       if sr_id and event_id and start_time:
           # Got SR ID from list - no need for full fetch
           kickoff = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
           if kickoff > now:
               events.append({
                   "sr_id": sr_id,
                   "kickoff": kickoff,
                   "platform_id": event_id,
               })
       elif event_id and start_time:
           # No SR ID in list - queue for full fetch
           betpawa_event_ids.append((event_id, kickoff))
   ```

2. Only fetch full events for items without SR ID in list response.

3. In the full event fetch (`fetch_full_event`), also try `widget.get("id")` first, then fall back to `widget.get("data", {}).get("matchId")`.

Also add a debug log showing whether SR IDs are found in list vs full fetch.
  </action>
  <verify>Run application - should now extract SR IDs from list response</verify>
  <done>BetPawa event parsing uses correct widget.id path like old working code</done>
</task>

<task type="auto">
  <name>Task 2: Verify discovery works and fix any remaining issues</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
1. Trigger a scrape and check logs:
   - "Discovered BetPawa events count=X" should show X > 0
   - Should be similar count to SportyBet/Bet9ja

2. If still 0 events, add more debug logging to find where events are lost:
   - Log `len(events_data)` after parsing responses
   - Log count of events with/without widgets
   - Log first event structure: `str(events_data[0])[:500]`

3. Fix any remaining issues found.
  </action>
  <verify>
Log shows: "Event discovery complete bet9ja=1162 betpawa=X sportybet=1219" where X > 0
  </verify>
  <done>BetPawa discovery returns events (count > 0)</done>
</task>

<task type="auto">
  <name>Task 3: Update issues file with resolution</name>
  <files>.planning/phases/42-validation-cleanup/42-01-FIX2-ISSUES.md</files>
  <action>
Move UAT-001 from "Open Issues" to "Resolved Issues" section with:
- Resolution date
- Commit hash
- Brief description of fix (used widget.id instead of widget.data.matchId)
  </action>
  <verify>Issues file shows UAT-001 in Resolved section</verify>
  <done>UAT-001 marked resolved</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] BetPawa discovers events (count > 0)
- [ ] Events have SR IDs for matching
- [ ] Other platforms still work (no regression)
- [ ] UAT-001 resolved in issues file
</verification>

<success_criteria>
- BetPawa event discovery returns events similar to other platforms
- Cross-platform matching works for BetPawa events
- No regression on SportyBet or Bet9ja discovery
</success_criteria>

<output>
After completion, create `.planning/phases/42-validation-cleanup/42-01-FIX3-SUMMARY.md`
</output>
