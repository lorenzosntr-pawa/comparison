---
phase: 93-odds-comparison-page
plan: 01
subsystem: web, api
tags: [filters, odds-comparison, competitor-events]
duration: 15 minutes
completed: 2026-02-12
---

# Phase 93-01 Summary: Tournament & Country Filters

## Performance Metrics
- Duration: 15 minutes
- Files modified: 3

## Accomplishments

### Task 1: Add Country Filter to Odds Comparison Page
- Added `countryFilter` field to `MatchFiltersState` interface
- Created country filter dropdown using Command + Popover pattern (consistent with existing league filter)
- Country filter extracts unique countries from tournaments data
- League dropdown is filtered by selected countries
- When country filter changes, tournament filter is automatically reset
- Updated `clearFilters` to reset country filter
- Updated `hasActiveFilters` to include `countryFilter.length > 0`

### Task 2: Fix Tournament Filter for Competitor-Only Events
- Added tournament name matching for competitor events query
- When `availability='competitor'` and `tournament_ids` provided:
  1. Query Tournament table to get tournament names for the provided IDs
  2. Filter CompetitorEvents where CompetitorTournament.name matches (case-insensitive)
- Uses `or_()` with `func.lower()` for case-insensitive matching

## Task Commits
| Task | Commit Hash |
|------|-------------|
| Task 1: Add country filter | `94780b3` |
| Task 2: Fix tournament filter | `5df84e6` |

## Files Modified
- `web/src/features/matches/components/match-filters.tsx` - Added country filter UI and logic
- `web/src/features/matches/index.tsx` - Updated DEFAULT_FILTERS with countryFilter
- `src/api/routes/events.py` - Added tournament name matching for competitor events

## Deviations from Plan
None.

## Issues Encountered
None.

## Verification
- [x] `npm run build` in web/ succeeds without errors
- [x] Country filter dropdown implemented with Command + Popover pattern
- [x] League filter shows only tournaments from selected countries
- [x] Tournament filter implemented for competitor availability mode via name matching
