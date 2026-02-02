---
phase: 42-validation-cleanup
plan: FIX7
type: fix
---

<objective>
Fix UAT-003: Odds Comparison API needs to load competitor odds from CompetitorOddsSnapshot table.

Source: 42-01-FIX5-ISSUES.md (UAT-003)
Priority: 1 blocker

Root cause: v1.7 stores competitor odds in `CompetitorOddsSnapshot` but the `/api/events` endpoint only loads from `OddsSnapshot`.
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
@src/api/routes/events.py
@src/db/models/competitor.py
</context>

<tasks>
<task type="auto">
  <name>Task 1: Add function to load competitor snapshots for matched events</name>
  <files>src/api/routes/events.py</files>
  <action>
Add a new function `_load_competitor_snapshots_for_events()` that:

1. Takes a list of BetPawa event_ids
2. Finds CompetitorEvents linked to those events (via betpawa_event_id)
3. Loads the latest CompetitorOddsSnapshot for each CompetitorEvent
4. Returns a dict mapping event_id -> source -> CompetitorOddsSnapshot

```python
async def _load_competitor_snapshots_for_events(
    db: AsyncSession,
    event_ids: list[int],
) -> dict[int, dict[str, CompetitorOddsSnapshot]]:
    """Load latest CompetitorOddsSnapshot for events that have competitor matches.

    Args:
        db: Async database session.
        event_ids: List of BetPawa event IDs.

    Returns:
        Dict mapping event_id -> {source: CompetitorOddsSnapshot}
        where source is 'sportybet' or 'bet9ja'
    """
    if not event_ids:
        return {}

    # Find CompetitorEvents linked to these BetPawa events
    comp_events_query = (
        select(CompetitorEvent)
        .where(CompetitorEvent.betpawa_event_id.in_(event_ids))
    )
    comp_events_result = await db.execute(comp_events_query)
    comp_events = comp_events_result.scalars().all()

    if not comp_events:
        return {}

    comp_event_ids = [ce.id for ce in comp_events]

    # Subquery to find latest snapshot per competitor_event_id
    latest_subq = (
        select(
            CompetitorOddsSnapshot.competitor_event_id,
            func.max(CompetitorOddsSnapshot.id).label("max_id"),
        )
        .where(CompetitorOddsSnapshot.competitor_event_id.in_(comp_event_ids))
        .group_by(CompetitorOddsSnapshot.competitor_event_id)
        .subquery()
    )

    # Load snapshots with markets
    snapshots_query = (
        select(CompetitorOddsSnapshot)
        .join(
            latest_subq,
            (CompetitorOddsSnapshot.competitor_event_id == latest_subq.c.competitor_event_id)
            & (CompetitorOddsSnapshot.id == latest_subq.c.max_id),
        )
        .options(selectinload(CompetitorOddsSnapshot.markets))
    )

    snapshots_result = await db.execute(snapshots_query)
    snapshots = snapshots_result.scalars().all()

    # Build mapping: comp_event_id -> snapshot
    snapshot_by_comp_event = {s.competitor_event_id: s for s in snapshots}

    # Build final mapping: betpawa_event_id -> source -> snapshot
    result: dict[int, dict[str, CompetitorOddsSnapshot]] = {}
    for ce in comp_events:
        snapshot = snapshot_by_comp_event.get(ce.id)
        if snapshot:
            if ce.betpawa_event_id not in result:
                result[ce.betpawa_event_id] = {}
            result[ce.betpawa_event_id][ce.source] = snapshot

    return result
```

Add necessary imports at top of file if not present:
- CompetitorEvent, CompetitorOddsSnapshot from src.db.models.competitor
  </action>
  <verify>Code compiles without errors</verify>
  <done>New function added to load competitor snapshots</done>
</task>

<task type="auto">
  <name>Task 2: Update _build_matched_event to include competitor odds</name>
  <files>src/api/routes/events.py</files>
  <action>
Modify `_build_matched_event()` to accept competitor snapshots and include them in the response:

1. Add parameter: `competitor_snapshots: dict[str, CompetitorOddsSnapshot] | None = None`

2. After building bookmaker odds from OddsSnapshot, also build from CompetitorOddsSnapshot:

```python
def _build_matched_event(
    event: Event,
    snapshots_by_bookmaker: dict[int, OddsSnapshot] | None = None,
    competitor_snapshots: dict[str, CompetitorOddsSnapshot] | None = None,
) -> MatchedEvent:
    """Map SQLAlchemy Event to Pydantic MatchedEvent.

    Args:
        event: Event model with loaded relationships.
        snapshots_by_bookmaker: Optional dict mapping bookmaker_id to latest OddsSnapshot.
        competitor_snapshots: Optional dict mapping source ('sportybet'/'bet9ja') to CompetitorOddsSnapshot.
    """
    snapshots_by_bookmaker = snapshots_by_bookmaker or {}
    competitor_snapshots = competitor_snapshots or {}

    bookmakers = []
    for link in event.bookmaker_links:
        # Check if this is a competitor bookmaker
        if link.bookmaker.slug in ("sportybet", "bet9ja"):
            # Use competitor snapshot
            comp_snapshot = competitor_snapshots.get(link.bookmaker.slug)
            inline_odds = _build_competitor_inline_odds(comp_snapshot)
            has_odds = bool(comp_snapshot and comp_snapshot.markets)
        else:
            # BetPawa - use regular snapshot
            snapshot = snapshots_by_bookmaker.get(link.bookmaker_id)
            inline_odds = _build_inline_odds(snapshot)
            has_odds = bool(snapshot and snapshot.markets)

        bookmakers.append(
            BookmakerOdds(
                bookmaker_slug=link.bookmaker.slug,
                bookmaker_name=link.bookmaker.name,
                external_event_id=link.external_event_id,
                event_url=link.event_url,
                has_odds=has_odds,
                inline_odds=inline_odds,
            )
        )
    # ... rest unchanged
```
  </action>
  <verify>Code compiles without errors</verify>
  <done>_build_matched_event now handles competitor snapshots</done>
</task>

<task type="auto">
  <name>Task 3: Update list_events to load and pass competitor snapshots</name>
  <files>src/api/routes/events.py</files>
  <action>
In the `list_events()` function, after loading BetPawa snapshots (line ~911), also load competitor snapshots:

```python
# Existing code:
event_ids = [event.id for event in events]
snapshots_by_event = await _load_latest_snapshots_for_events(db, event_ids)

# Add this:
competitor_snapshots_by_event = await _load_competitor_snapshots_for_events(db, event_ids)

# Update the matched_events list comprehension:
matched_events = [
    _build_matched_event(
        event,
        snapshots_by_event.get(event.id),
        competitor_snapshots_by_event.get(event.id),
    )
    for event in events
]
```
  </action>
  <verify>Code compiles without errors</verify>
  <done>list_events loads and passes competitor snapshots</done>
</task>

<task type="auto">
  <name>Task 4: Test odds comparison page</name>
  <files>None (testing)</files>
  <action>
1. Restart the backend: `python -m uvicorn "src.api.app:create_app" --factory --reload --port 8000`

2. Navigate to Odds Comparison page in browser

3. Verify:
   - Events show BetPawa odds
   - Events show SportyBet odds (where available)
   - Events show Bet9ja odds (where available)
   - Multiple bookmaker columns display side-by-side
  </action>
  <verify>Odds Comparison page shows BetPawa + competitor odds</verify>
  <done>All bookmaker odds displayed correctly</done>
</task>
</tasks>

<verification>
Before declaring plan complete:
- [ ] Code compiles without errors
- [ ] Backend starts without import errors
- [ ] Odds Comparison page shows BetPawa odds
- [ ] Odds Comparison page shows competitor odds where available
- [ ] Events with all 3 bookmakers show all 3 sets of odds
</verification>

<success_criteria>
- UAT-003 addressed: API loads competitor odds from correct table
- Odds Comparison page shows all available bookmaker odds side-by-side
- Ready for final user acceptance testing
</success_criteria>

<output>
After completion, create `.planning/phases/42-validation-cleanup/42-01-FIX7-SUMMARY.md`
</output>
