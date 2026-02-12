# UAT Issues: Phase 93 Plan 01

**Tested:** 2026-02-12
**Source:** .planning/phases/93-odds-comparison-page/93-01-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-001: Country filter should directly filter events list

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12
**Phase/Plan:** 93-01-FIX
**Severity:** Minor
**Type:** Enhancement
**Feature:** Country filter
**Description:** Country filter currently only narrows the league/tournament dropdown. User expects it to also directly filter the events list by country/region.
**Expected:** Selecting a country filters both the league dropdown AND the events displayed
**Actual:** Country filter only affects which tournaments appear in the league dropdown
**Resolution:** Added `countries` parameter to `/events` API endpoint. Backend filters events by Tournament.country (BetPawa) and CompetitorTournament.country (competitor-only). Frontend passes countryFilter to useMatches hook.

### UAT-002: Filter dropdowns should scope to current availability mode

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12
**Phase/Plan:** 93-01-FIX
**Severity:** Minor
**Type:** Enhancement
**Feature:** Filter dropdowns (country, tournament)
**Description:** When viewing competitor-only events, the filter dropdowns still show all available countries/tournaments instead of only those with competitor data.
**Expected:** In competitor-only mode, country and tournament filters show only options where competitor events exist
**Actual:** Dropdowns show all available data regardless of availability mode selection
**Resolution:** Added `availability` parameter to `/events/tournaments` endpoint. For competitor mode, returns only BetPawa tournaments that match competitor tournament names with upcoming competitor-only events. Frontend passes availability to useTournaments hook.

---

*Phase: 93-odds-comparison-page*
*Plan: 01*
*Tested: 2026-02-12*
