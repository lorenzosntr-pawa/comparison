---
phase: 01-market-mapping-port
plan: 06
subsystem: api
tags: [unified-api, pytest, testing, discriminated-union]

# Dependency graph
requires:
  - phase: 01-market-mapping-port
    provides: Sportybet mapper, Bet9ja mapper, market registry, parsers
provides:
  - Unified map_to_betpawa entry point
  - Public API exports from package root
  - pytest test suite with 83 tests
affects: [phase-2-database, scraper-integration]

# Tech tracking
tech-stack:
  added: [pytest>=8.0]
  patterns: [discriminated-union-dispatch, editable-install]

key-files:
  created:
    - src/market_mapping/mappers/unified.py
    - src/pyproject.toml
    - tests/__init__.py
    - tests/test_parsers.py
    - tests/test_mappings.py
    - tests/test_sportybet_mapper.py
    - tests/test_bet9ja_mapper.py
  modified:
    - src/market_mapping/__init__.py
    - src/market_mapping/mappers/__init__.py
    - src/market_mapping/types/competitors.py

key-decisions:
  - "Bet9jaInput accepts full odds dict for batch processing (not single key/odds)"
  - "map_to_betpawa returns MappedMarket | list[MappedMarket] based on source"

patterns-established:
  - "Unified API dispatches based on discriminated union source field"
  - "pytest with pythonpath configuration for src layout"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-20
---

# Phase 1 Plan 6: Unified API & Tests Summary

**Unified map_to_betpawa entry point with discriminated union dispatch and 83 passing pytest tests**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-20T12:04:00Z
- **Completed:** 2026-01-20T12:12:00Z
- **Tasks:** 2 (+ 1 verification checkpoint)
- **Files modified:** 10

## Accomplishments

- Unified `map_to_betpawa` entry point that dispatches based on source field
- Updated `Bet9jaInput` to accept full odds dict for batch processing
- Exported all public API from `market_mapping` package root
- pytest test suite with 83 passing tests covering parsers, mappings, and both mappers
- Phase 1 complete with 108 market mappings available

## Task Commits

Each task was committed atomically:

1. **Task 1: Port unified mapper and package exports** - `49b4ae0` (feat)
2. **Task 2: Set up pytest and write unit tests** - `6a571a3` (test)

**Plan metadata:** (this commit) (docs: complete plan)

## Files Created/Modified

- `src/market_mapping/mappers/unified.py` - Unified entry point with discriminated union dispatch
- `src/market_mapping/__init__.py` - Public API exports
- `src/market_mapping/mappers/__init__.py` - Added map_to_betpawa export
- `src/market_mapping/types/competitors.py` - Updated Bet9jaInput for batch processing
- `src/pyproject.toml` - Package metadata and pytest configuration
- `tests/__init__.py` - Test package initialization
- `tests/test_parsers.py` - 16 tests for specifier and Bet9ja key parsing
- `tests/test_mappings.py` - 25 tests for market registry and lookups
- `tests/test_sportybet_mapper.py` - 21 tests for Sportybet market mapping
- `tests/test_bet9ja_mapper.py` - 21 tests for Bet9ja market mapping

## Decisions Made

- Changed `Bet9jaInput` from single key/odds to full odds dict to align with batch processing API
- `map_to_betpawa` returns different types based on source (single MappedMarket for Sportybet, list for Bet9ja)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Next Phase Readiness

Phase 1 complete:
- 108 market mappings from Sportybet and Bet9ja to Betpawa
- Unified API for any competitor source
- 83 passing tests validating all functionality
- Ready for Phase 2: Database Schema

---
*Phase: 01-market-mapping-port*
*Completed: 2026-01-20*
