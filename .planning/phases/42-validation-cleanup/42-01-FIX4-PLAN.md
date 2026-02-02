---
phase: 42-validation-cleanup
plan: 01-FIX4
type: fix
---

<objective>
Fix two critical v1.7 bugs reported in UAT:

**BUG-001: BetPawa events not matching with competitors**
- Coverage page shows 0 BetPawa events
- Odds comparison shows only competitor odds
- Competitors match each other (SportyBet-Bet9ja) but not BetPawa
- Hypothesis: FIX3 used `widget.id` which may be a widget UUID, not the actual SportRadar ID

**BUG-002: Tournament/region missing for competitors**
- Coverage page shows "-" for competitor tournament regions
- Odds comparison Region column blank for SportyBet/Bet9ja events
- Root cause: Competitor events use fallback tournaments with null country_raw
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-phase.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/ROADMAP.md
@.planning/ISSUES.md

**Current implementation:**
@src/scraping/event_coordinator.py

**Key areas to investigate:**

1. BetPawa SR ID extraction (lines 317-324, 363-371):
   - Currently uses `widget.get("id")` first
   - Falls back to `widget.get("data", {}).get("matchId")`
   - Need to verify what each field actually contains

2. Competitor event creation (lines 1509-1577):
   - Uses fallback tournaments with no country data
   - Should use proper tournament from tournament_id mapping

3. Competitor tournament creation during scraping:
   - Need to extract country from raw_data like we do for BetPawa
</context>

<tasks>

<task type="manual">
  <name>Task 1: Debug BetPawa widget structure</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
Add temporary debug logging to capture what `widget.id` and `widget.data.matchId` actually contain.

In `_discover_betpawa()` after finding the SPORTRADAR widget (around line 316), add:

```python
if widget.get("type") == "SPORTRADAR":
    widget_id = widget.get("id")
    widget_data = widget.get("data", {})
    widget_match_id = widget_data.get("matchId")
    logger.warning(
        "DEBUG BetPawa widget SR ID sources",
        widget_id=widget_id,
        widget_match_id=widget_match_id,
        widget_id_type=type(widget_id).__name__,
        widget_match_id_type=type(widget_match_id).__name__,
    )
    # ... rest of extraction
```

Run a scrape and check logs to see:
- What format is `widget.id`? (numeric like "12345678" or UUID like "abc-123-def"?)
- What format is `widget.data.matchId`?
- Which matches the competitor SR ID format?
  </action>
  <verify>Logs show both values for comparison</verify>
  <done>Know which field contains actual SportRadar ID</done>
</task>

<task type="auto">
  <name>Task 2: Fix BetPawa SR ID extraction based on debug findings</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
Based on Task 1 findings, fix the SR ID extraction.

**If widget.id is wrong (UUID) and widget.data.matchId is correct (numeric):**
Reverse the priority - use `widget.data.matchId` first, fall back to `widget.id`:

```python
for widget in widgets:
    if widget.get("type") == "SPORTRADAR":
        # Use widget.data.matchId first (actual SR ID)
        widget_data = widget.get("data", {})
        sr_id = widget_data.get("matchId")
        if not sr_id:
            # Fall back to widget.id (may work for some events)
            sr_id = widget.get("id")
        if sr_id:
            sr_id = str(sr_id)
        break
```

Apply this fix in both locations:
1. List response parsing (around lines 315-324)
2. Full event fetch (around lines 361-371)

Also remove the debug logging added in Task 1.
  </action>
  <verify>Scrape shows BetPawa events with SR IDs that match competitor format</verify>
  <done>BetPawa SR ID extraction uses correct field</done>
</task>

<task type="auto">
  <name>Task 3: Fix competitor tournament creation to include country</name>
  <files>src/scraping/event_coordinator.py</files>
  <action>
Update `_create_competitor_event_from_raw()` to extract tournament info from raw_data and create proper tournaments with country data.

For SportyBet, extract from raw_data:
- Tournament name: `raw_data.get("tournamentName")`
- Category/region: `raw_data.get("categoryName")` (this is the country)
- Tournament ID: `raw_data.get("tournamentId")`

For Bet9ja, extract from raw_data:
- Tournament comes from the group structure
- Country may be in `raw_data.get("COUNTRY")` or parent group

Create new helper method `_get_or_create_competitor_tournament_from_raw()`:

```python
async def _get_or_create_competitor_tournament_from_raw(
    self,
    db: AsyncSession,
    source: CompetitorSource,
    raw_data: dict,
    sport_id: int,
) -> int:
    """Get or create CompetitorTournament from raw API response."""
    if source == CompetitorSource.SPORTYBET:
        tournament_name = raw_data.get("tournamentName", "Unknown")
        country_raw = raw_data.get("categoryName")
        external_id = raw_data.get("tournamentId", "")
    else:  # BET9JA
        # Bet9ja has different structure
        tournament_name = raw_data.get("GN", "Unknown")  # Group name
        country_raw = raw_data.get("SGN")  # Sport group name (often country)
        external_id = str(raw_data.get("GID", ""))  # Group ID

    if not external_id:
        external_id = f"unknown-{source.value}-{tournament_name}"

    # Try to find existing tournament
    result = await db.execute(
        select(CompetitorTournament.id).where(
            CompetitorTournament.source == source.value,
            CompetitorTournament.external_id == external_id,
        )
    )
    row = result.first()
    if row:
        return row[0]

    # Create new tournament with country
    tournament = CompetitorTournament(
        source=source.value,
        sport_id=sport_id,
        name=tournament_name,
        external_id=external_id,
        country_raw=country_raw,
        sportradar_id=None,
    )
    db.add(tournament)
    await db.flush()

    logger.debug(
        "Created competitor tournament from raw data",
        source=source.value,
        name=tournament_name,
        country_raw=country_raw,
    )

    return tournament.id
```

Then update `store_batch_results()` to use this method instead of fallback tournament:

Replace line ~1126:
```python
tournament_id=fallback_competitor_tournament_ids[source],
```

With:
```python
tournament_id=await self._get_or_create_competitor_tournament_from_raw(
    db=db,
    source=source,
    raw_data=raw_data,
    sport_id=sport_id,
),
```
  </action>
  <verify>Competitor events created with proper tournament including country_raw</verify>
  <done>Competitor events have tournament with country data</done>
</task>

<task type="auto">
  <name>Task 4: Clear stale data and run fresh scrape</name>
  <files>None (database operation)</files>
  <action>
The existing data has incorrect SR IDs and fallback tournaments. Clear it and run fresh:

1. Clear events and competitor events with fallback tournaments:
```sql
-- Check current state
SELECT COUNT(*) FROM events;
SELECT COUNT(*) FROM competitor_events;
SELECT COUNT(*) FROM tournaments WHERE name = 'Discovered Events';
SELECT COUNT(*) FROM competitor_tournaments WHERE name = 'Discovered Events';

-- Clear stale data (preserves tournament discovery data, only clears scrape results)
DELETE FROM odds_snapshots;
DELETE FROM competitor_odds_snapshots;
DELETE FROM event_scrape_status;
DELETE FROM event_bookmakers;
DELETE FROM events WHERE tournament_id IN (SELECT id FROM tournaments WHERE name = 'Discovered Events');
DELETE FROM competitor_events WHERE tournament_id IN (SELECT id FROM competitor_tournaments WHERE name = 'Discovered Events');
DELETE FROM tournaments WHERE name = 'Discovered Events';
DELETE FROM competitor_tournaments WHERE name = 'Discovered Events';
```

2. Trigger a fresh scrape via the UI or API:
   - POST /api/scrape/start
   - Wait for completion

3. Check coverage page:
   - BetPawa events should now show > 0
   - Matched events should appear
   - Tournament regions should populate
  </action>
  <verify>Coverage page shows BetPawa events matched with competitors</verify>
  <done>Fresh scrape with correct data</done>
</task>

<task type="auto">
  <name>Task 5: Update ISSUES.md with resolution</name>
  <files>.planning/ISSUES.md</files>
  <action>
Add BUG-001 and BUG-002 to the Closed section with resolution notes.

Add to "## Closed Enhancements" section (after ISS-004):

```markdown
### BUG-001: BetPawa events not matching with competitors (RESOLVED)
**Discovered:** v1.7 UAT - 2026-02-02
**Resolution:** Fixed 2026-02-02 - SR ID extraction was using `widget.id` (widget UUID) instead of `widget.data.matchId` (actual SportRadar ID). Reversed the priority in event_coordinator.py.

### BUG-002: Tournament/region missing for competitors (RESOLVED)
**Discovered:** v1.7 UAT - 2026-02-02
**Resolution:** Fixed 2026-02-02 - Competitor events were using fallback tournaments with null country. Added `_get_or_create_competitor_tournament_from_raw()` to extract proper tournament info including country from raw API responses.
```
  </action>
  <verify>ISSUES.md updated with resolutions</verify>
  <done>Issues documented as resolved</done>
</task>

<task type="auto">
  <name>Task 6: Update STATE.md with FIX4 completion</name>
  <files>.planning/STATE.md</files>
  <action>
Update STATE.md to reflect FIX4 completion:

1. Update "Last activity" line:
```
Last activity: 2026-02-02 — Completed 42-01-FIX4.md (BetPawa matching & competitor tournaments fix)
```

2. Add to "Key Patterns" section:
```
- **BetPawa SR ID from widget.data.matchId** - The widget.id is a widget UUID, actual SR ID is in widget.data.matchId (v1.7 FIX4)
- **Competitor tournament from raw data** - Extract tournament name and country from competitor raw responses, not fallback (v1.7 FIX4)
```

3. Update "Session Continuity" section:
```
Last session: 2026-02-02
Stopped at: Completed 42-01-FIX4.md (BetPawa matching & competitor tournaments fix)
Resume file: None
```
  </action>
  <verify>STATE.md reflects current status</verify>
  <done>STATE.md updated</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] Debug logging shows what widget.id vs widget.data.matchId contain
- [ ] SR ID extraction uses correct field (likely widget.data.matchId)
- [ ] BetPawa events match with competitors on coverage page
- [ ] Competitor events have tournaments with country_raw populated
- [ ] Odds comparison shows BetPawa odds alongside competitors
- [ ] ISSUES.md updated with BUG-001 and BUG-002 resolutions
- [ ] STATE.md updated with FIX4 completion
</verification>

<success_criteria>
- Coverage page shows BetPawa events > 0
- Matched events show all three platforms
- Tournament regions display for competitors (not "-")
- Odds comparison shows BetPawa and competitor odds together
</success_criteria>

<output>
After completion, create `.planning/phases/42-validation-cleanup/42-01-FIX4-SUMMARY.md`
</output>
