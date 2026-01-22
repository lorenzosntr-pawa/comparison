---
phase: 10-matches-page-improvements
plan: 01
type: execute
---

<objective>
Add team search API endpoint and region/country display to match table.

Purpose: Enable searching by team name and show match context (league + region) without clicking into details.
Output: Working search query parameter on events API, region column in match table.
</objective>

<execution_context>
~/.claude/get-shit-done/workflows/execute-phase.md
~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/10-matches-page-improvements/10-CONTEXT.md

**Key files:**
@src/api/routes/events.py
@src/matching/schemas.py
@src/db/models/sport.py
@web/src/features/matches/components/match-table.tsx
@web/src/features/matches/hooks/use-matches.ts
@web/src/types/api.ts

**Prior phase context:**
- Phase 07-02: Created match list table with filters, pagination, column settings
- Tournament model has `country` field (nullable string) for region info
- Events API already has tournament_id, kickoff_from/to, min_bookmakers filters
- TanStack Query pattern: staleTime=30s, gcTime=60s, refetchInterval=60s
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add search query parameter to events API</name>
  <files>src/api/routes/events.py</files>
  <action>
Add `search: str | None = Query(default=None, description="Search by team name (home or away)")` parameter to the `list_events` endpoint.

In the query building section, add filter:
```python
if search:
    search_pattern = f"%{search}%"
    query = query.where(
        (Event.home_team.ilike(search_pattern)) |
        (Event.away_team.ilike(search_pattern))
    )
    count_query = count_query.where(
        (Event.home_team.ilike(search_pattern)) |
        (Event.away_team.ilike(search_pattern))
    )
```

Use `ilike` for case-insensitive search. Apply to both home_team and away_team fields with OR logic.
  </action>
  <verify>
curl "http://localhost:8000/api/events?search=arsenal" returns events where either team contains "arsenal" (case-insensitive).
curl "http://localhost:8000/api/events?search=chelsea" returns events with Chelsea in home or away team.
  </verify>
  <done>Search parameter filters events by team name substring match, case-insensitive, returns matching events.</done>
</task>

<task type="auto">
  <name>Task 2: Add region column to match table</name>
  <files>src/matching/schemas.py, src/api/routes/events.py, web/src/types/api.ts, web/src/features/matches/components/match-table.tsx</files>
  <action>
**Backend changes:**

1. In `src/matching/schemas.py`, add `tournament_country: str | None = None` field to `MatchedEvent` model (after tournament_name).

2. In `src/api/routes/events.py`, update `_build_matched_event` to include:
   ```python
   tournament_country=event.tournament.country,
   ```

**Frontend changes:**

3. In `web/src/types/api.ts`, add `tournament_country: string | null` to `MatchedEvent` interface.

4. In `web/src/features/matches/components/match-table.tsx`:
   - Add a "Region" column header after "Tournament" column
   - Add table cell that displays `event.tournament_country ?? '-'`
   - Keep it compact with `text-sm text-muted-foreground` styling to match Tournament column
  </action>
  <verify>
Match table displays Region column showing tournament country (or "-" if null).
API response includes tournament_country field for each event.
  </verify>
  <done>Region column visible in match table, shows country/region for each match's tournament.</done>
</task>

</tasks>

<verification>
Before declaring plan complete:
- [ ] `curl "http://localhost:8000/api/events?search=test"` returns filtered results
- [ ] `curl "http://localhost:8000/api/events"` includes `tournament_country` in response
- [ ] Match table shows Region column with country values
- [ ] No TypeScript errors: `cd web && npm run build`
</verification>

<success_criteria>
- Search query parameter works for team name filtering
- Tournament country/region visible in match table
- No regressions to existing filters
- Build passes
</success_criteria>

<output>
After completion, create `.planning/phases/10-matches-page-improvements/10-01-SUMMARY.md`
</output>
