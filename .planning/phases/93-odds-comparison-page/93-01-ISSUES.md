# UAT Issues: Phase 93 Plan 01

**Tested:** 2026-02-12 (re-test after FIX2)
**Source:** .planning/phases/93-odds-comparison-page/93-01-SUMMARY.md, 93-01-FIX-SUMMARY.md, 93-01-FIX2-SUMMARY.md
**Tester:** User via /gsd:verify-work

## Open Issues

[None]

## Resolved Issues

### UAT-006: Countries endpoint crashes in competitor mode

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12 in 93-01-FIX3
**Phase/Plan:** 93-01-FIX2
**Severity:** Blocker
**Feature:** Country filter in competitor-only mode
**Description:** The `/api/events/countries?availability=competitor` endpoint returns a 500 Internal Server Error.
**Root Cause:** `CompetitorTournament` model has `country_raw` attribute, not `country`. The endpoint incorrectly referenced `CompetitorTournament.country`.
**Resolution:** Changed 3 references to use `country_raw` instead of `country` in the `list_countries` function.
**Commit:** `bb3a2e8`

### UAT-003: Country filter doesn't scope to availability mode

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12 in FIX2 + FIX3
**Phase/Plan:** 93-01
**Severity:** Major
**Feature:** Country filter dropdown
**Description:** When in competitor-only mode, the country filter still shows ALL countries instead of only countries with competitor events.
**Resolution:** Added `/events/countries` endpoint with availability parameter (FIX2) + fixed attribute name (FIX3)

### UAT-004: API 500 error when filtering in competitor-only mode

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12 in 93-01-FIX2
**Phase/Plan:** 93-01
**Severity:** Blocker
**Feature:** Tournament filter in competitor-only mode
**Description:** Selecting a tournament filter in competitor-only mode sometimes causes a 500 API error.
**Resolution:** Added early return with empty MatchedEventList when tournament_names is empty but tournament_ids provided.

### UAT-005: Filter state not preserved per availability mode (Enhancement)

**Discovered:** 2026-02-12
**Resolved:** 2026-02-12 in 93-01-FIX2
**Phase/Plan:** 93-01
**Severity:** Minor
**Type:** Enhancement
**Feature:** Filter state management
**Description:** Switching between modes would reset all filters.
**Resolution:** Implemented per-mode filter state with separate useState hooks for betpawaFilters and competitorFilters.

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
*Tested: 2026-02-12 (re-test)*
