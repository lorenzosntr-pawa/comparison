---
phase: 87-investigation-schema-design
plan: 01
subsystem: database
tags: [availability, schema-design, investigation, cache, api]

# Dependency graph
requires:
  - phase: 86
    provides: v2.4 Historical Analytics complete
provides:
  - Availability tracking design specification
  - Schema design for unavailable_at timestamp
  - Detection logic specification
  - API response schema specification
affects: [88-backend-availability, 89-api-cache, 90-odds-comparison-ui, 91-event-details-ui, 92-history-charts]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "unavailable_at timestamp pattern: nullable timestamp to track when market became unavailable"
    - "Cache-level availability detection: compare new scrape to previous cache state"
    - "API availability response: available boolean + unavailable_since timestamp"

key-files:
  created:
    - .planning/phases/87-investigation-schema-design/DISCOVERY.md

key-decisions:
  - "Option B selected: unavailable_at timestamp column (not boolean, not separate table)"
  - "Detection at cache layer: compare previous cache to new scrape results"
  - "UI distinction: dash for never_offered vs strikethrough for became_unavailable"

patterns-established:
  - "Availability tracking via nullable timestamp: NULL = available, timestamp = unavailable since"
  - "Cache comparison pattern: detect absences by comparing market keys"

issues-created: []

# Metrics
duration: 18min
completed: 2026-02-11
---

# Phase 87 Plan 01: Investigation & Schema Design Summary

**Discovered markets disappear over time (15-56% presence), designed unavailable_at timestamp approach with cache-level detection**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-11T15:00:00Z
- **Completed:** 2026-02-11T15:18:00Z
- **Tasks:** 2
- **Files modified:** 1 (DISCOVERY.md created)

## Accomplishments

- Analyzed current data patterns: 56.8% snapshot coverage ratio, 15-30% market presence for specialized markets
- Found outcome suspensions very rare (0.0474%) - already handled with is_active=false
- Identified gap between "never offered" (null) and "became unavailable" (needs tracking)
- Selected Option B: unavailable_at timestamp column on MarketOdds/CompetitorMarketOdds
- Designed cache-level detection logic comparing previous state to new scrape
- Specified API response schema with available boolean and unavailable_since timestamp

## Task Commits

1. **Task 1+2: Investigate patterns and design schema** - `da02a5e` (docs)

**Plan metadata:** (this commit)

## Files Created/Modified

- `.planning/phases/87-investigation-schema-design/DISCOVERY.md` - Complete analysis and design specification

## Decisions Made

1. **Option B (unavailable_at timestamp)** over alternatives:
   - Not boolean: Timestamp tells us WHEN, enables "since X" tooltips
   - Not separate table: Too much overhead for rare events
   - Not cache-only: Would lose state on restart

2. **Detection at cache layer**: Compare market keys in previous cache vs new scrape - if present before but missing now, mark unavailable

3. **UI distinction**:
   - `null` market (never offered): Plain dash "-"
   - `available=false` (became unavailable): Strikethrough dash with tooltip

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - data analysis and design proceeded smoothly.

## Next Phase Readiness

- Phase 88 can implement schema migration and detection logic based on DISCOVERY.md specification
- No blockers - design is complete and implementation path is clear

---
*Phase: 87-investigation-schema-design*
*Completed: 2026-02-11*
