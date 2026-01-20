---
phase: 01-market-mapping-port
plan: 04
subsystem: mapping
tags: [sportybet, mapping, pydantic, errors]

# Dependency graph
requires:
  - phase: 01-market-mapping-port
    provides: Type definitions (sportybet.py, mapped.py, normalized.py, errors.py)
  - phase: 01-market-mapping-port
    provides: Market mappings registry (find_by_sportybet_id, is_*_market helpers)
  - phase: 01-market-mapping-port
    provides: Parser utilities (parse_specifier, ParsedHandicap)
provides:
  - map_sportybet_to_betpawa function
  - Sportybet market transformation to Betpawa format
  - Structured MappingError exceptions for all failure cases
affects: [bet9ja-mapper, scraper-integration, event-matching]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Raise MappingError instead of returning Result/None
    - Case-insensitive outcome matching with position fallback
    - Separate helpers for simple/O-U/handicap market types

key-files:
  created:
    - src/market_mapping/mappers/__init__.py
    - src/market_mapping/mappers/sportybet.py
  modified: []

key-decisions:
  - "Raise exceptions vs return None: Using MappingError for all failure cases provides actionable error info"
  - "Outcome matching order: desc match first (case-insensitive), then position fallback"
  - "Tuple for outcomes: MappedMarket.outcomes uses tuple for immutability"

patterns-established:
  - "_map_* private helpers for market-type-specific logic"
  - "frozenset for constant market ID classifications (TIME_BASED_MARKET_IDS)"

issues-created: []

# Metrics
duration: 8min
completed: 2026-01-20
---

# Plan 01-04 Summary: Sportybet Mapper

**Complete Sportybet-to-Betpawa transformation with structured error handling for simple, O/U, handicap, and variant markets**

## Performance

- **Duration:** 8 min
- **Started:** 2026-01-20T12:00:00Z
- **Completed:** 2026-01-20T12:08:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Ported complete Sportybet mapper from TypeScript to Python
- Outcome matching by description (case-insensitive) with position fallback
- Support for all market types: simple, Over/Under with line, Handicap with values, Variant
- Structured MappingError exceptions with appropriate error codes

## Task Commits

Each task was committed atomically:

1. **Task 1: Port outcome mapping logic** - `75587a9` (feat)
2. **Task 2: Port market mapping functions** - `92e7161` (feat)

**Plan metadata:** (pending)

## Files Created/Modified

### Created
- `src/market_mapping/mappers/__init__.py` - Module exports (map_sportybet_to_betpawa)
- `src/market_mapping/mappers/sportybet.py` - Full Sportybet mapper implementation

## Decisions Made

1. **Exception-based error handling**: Instead of returning None or Result types (as in TypeScript), raising MappingError provides detailed context for debugging and programmatic error handling.

2. **Outcome matching strategy**: Try case-insensitive description match first, fall back to position-based matching. This handles variations in outcome descriptions across API versions.

3. **TIME_BASED_MARKET_IDS constant**: Added frozenset for markets like "10 Minutes 1X2" that have time specifiers but should be treated as simple markets.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

Plan 01-04 complete. The Sportybet mapper is fully functional:
- All market types supported (simple, O/U, handicap, variant)
- Structured error codes for all failure scenarios
- Ready for Bet9ja mapper (01-05)

---
*Phase: 01-market-mapping-port*
*Completed: 2026-01-20*
