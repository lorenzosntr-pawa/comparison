---
phase: 100-investigation-design
plan: 01
subsystem: market-mapping
tags: [audit, design, schema, api, architecture]

# Dependency graph
requires:
  - phase: 45-market-mapping-improvement-audit
    provides: mapping success rates (52.2%/40.5%), gap prioritization
provides:
  - Gap analysis with current coverage statistics
  - 3-table DB schema design (user_market_mappings, mapping_audit_log, unmapped_market_log)
  - Runtime merge strategy (code + DB with priority)
  - Complete API contract specification for CRUD, discovery, and analysis
  - Pydantic schema outlines following project conventions
affects: [101, 102, 103, 104, 105, 106]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Runtime merge strategy: code base + DB overrides"
    - "Hot reload API endpoint for cache invalidation"
    - "Audit log pattern for change tracking"
    - "Unmapped market discovery with status workflow"

key-files:
  created:
    - .planning/phases/100-investigation-design/INVESTIGATION.md
    - .planning/phases/100-investigation-design/DESIGN.md

key-decisions:
  - "3 tables: user_market_mappings (CRUD), mapping_audit_log (history), unmapped_market_log (discovery)"
  - "Runtime merge: DB mappings override code mappings with same canonical_id"
  - "Priority field for handling multiple DB mappings with same betpawa_id"
  - "Soft delete via is_active flag (no hard deletes)"
  - "Unmapped status workflow: NEW → ACKNOWLEDGED → MAPPED/IGNORED"

patterns-established:
  - "Cache-first merged mappings with hot reload"
  - "Audit log with old/new value JSONB for change tracking"
  - "Unmapped market occurrence counting for prioritization"

issues-created: []

# Metrics
duration: 18min
completed: 2026-02-13
---

# Phase 100 Plan 01: Investigation & Design Summary

**Gap analysis of 266k+ competitor snapshots and comprehensive architecture design for user-editable market mapping utility with 3-table schema, runtime merge, and complete API specification**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-13T14:00:00Z
- **Completed:** 2026-02-13T14:18:00Z
- **Tasks:** 2
- **Files created:** 2

## Accomplishments

- Analyzed 266,614 competitor snapshots (136k SportyBet, 130k Bet9ja) across 11 days of data
- Documented 103 unique betpawa_market_id mappings from 129 code definitions
- Identified top unmapped markets (player props 800117, 775-777; combo markets CHANCEMIX)
- Designed 3-table schema: user_market_mappings, mapping_audit_log, unmapped_market_log
- Specified runtime merge strategy with code base + DB overrides
- Defined complete API contracts for 12 endpoints (CRUD, discovery, analysis)
- Outlined Pydantic schemas following project conventions (camelCase, from_attributes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Gap analysis** - `3bda2b8` (feat)
2. **Task 2: Architecture design** - `c0a5360` (feat)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `.planning/phases/100-investigation-design/INVESTIGATION.md` - Gap analysis with SQL-derived statistics
- `.planning/phases/100-investigation-design/DESIGN.md` - Complete technical specification

## Decisions Made

1. **3-table schema:** Separate tables for user mappings (CRUD), audit log (history), and unmapped markets (discovery) - clean separation of concerns
2. **Runtime merge strategy:** Code MARKET_MAPPINGS as base, DB user_market_mappings as overrides, merged at startup with hot reload capability
3. **Priority system:** Higher priority DB mappings win when multiple map to same betpawa_id
4. **Soft delete:** is_active flag instead of hard delete - preserves audit trail
5. **Unmapped workflow:** NEW → ACKNOWLEDGED → MAPPED/IGNORED status progression for discovered markets

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - investigation and design completed successfully.

## Next Phase Readiness

Ready for Phase 101: Backend Foundation
- Implement Alembic migration for 3 tables
- Create SQLAlchemy ORM models
- Build MappingCache with hot reload
- Implement CRUD repository

---

*Phase: 100-investigation-design*
*Completed: 2026-02-13*
