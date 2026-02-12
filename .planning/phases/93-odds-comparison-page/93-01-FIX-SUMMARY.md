# Summary: Phase 93 Plan 01-FIX

**Phase:** 93-odds-comparison-page
**Plan:** 01-FIX (UAT Enhancement Fixes)
**Completed:** 2026-02-12
**Duration:** ~10 min

## What Was Built

Fixed 2 UAT enhancement issues from 93-01-ISSUES.md:

### UAT-001: Country filter directly filters events list

Added `countries` parameter to the `/events` API endpoint:
- Backend: `countries: list[str] | None = Query(None)` parameter accepts country names
- For BetPawa events: filters via `Event.tournament.country IN countries`
- For competitor events: filters via `CompetitorEvent.tournament.country IN countries`
- Case-insensitive matching using `func.lower()`
- Frontend: wired `countryFilter` from MatchFiltersState to useMatches hook

**Commit:** `151d77c` - feat(93-01): add country filter to events API endpoint

### UAT-002: Filter dropdowns scope to availability mode

Added `availability` parameter to the `/events/tournaments` endpoint:
- For `competitor` mode: returns only BetPawa tournaments that have matching competitor-only events (by tournament name)
- Added time filter to only consider upcoming events
- Frontend: useTournaments hook accepts `availability` parameter, MatchFilters passes current mode

**Commit:** `6701b14` - feat(93-01): scope filter dropdowns to availability mode

## Files Changed

**Backend:**
- [events.py](src/api/routes/events.py) - Added countries filter to list_events, availability filter to list_tournaments

**Frontend:**
- [api.ts](web/src/lib/api.ts) - Added countries param to getEvents, availability param to getTournaments
- [use-matches.ts](web/src/features/matches/hooks/use-matches.ts) - Added countries to UseMatchesParams
- [use-tournaments.ts](web/src/features/matches/hooks/use-tournaments.ts) - Added availability to UseTournamentsParams
- [match-filters.tsx](web/src/features/matches/components/match-filters.tsx) - Pass availability to useTournaments
- [index.tsx](web/src/features/matches/index.tsx) - Pass countryFilter to useMatches

## Verification

- [x] `npm run build` succeeds
- [x] Country filter affects events list directly (not just tournament dropdown)
- [x] Filter dropdowns scope to current availability mode

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `151d77c` | feat | Add country filter to events API endpoint |
| `6701b14` | feat | Scope filter dropdowns to availability mode |

## Notes

Both enhancements are now live. The country filter provides more intuitive filtering (affects both dropdowns AND the events list), and the availability-scoped dropdowns reduce noise when viewing competitor-only events.
