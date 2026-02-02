---
phase: 43-market-mapping-audit
plan: 01
subsystem: market-mapping
tags: [audit, mapping, sportybet, bet9ja, analysis]

# Dependency graph
requires:
  - phase: 01-market-structure-analysis
    provides: initial market mappings (108 markets)
provides:
  - Comprehensive audit of mapping gaps across all platforms
  - 380 unique unmapped market types identified
  - Categorized and prioritized fix recommendations
affects: [44, 45, 46]  # Future fix phases

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Async SQLAlchemy for event fetching"
    - "Pydantic for SportyBet market validation"

key-files:
  created:
    - src/scripts/audit_market_mapping.py
    - .planning/phases/43-market-mapping-audit/AUDIT-FINDINGS.md
    - .planning/phases/43-market-mapping-audit/audit_raw_data.json

key-decisions:
  - "Analyzed 100 events across 46 tournaments and 32 countries for diversity"
  - "Categorized unmapped markets by inferred type (Goals, Cards, Corners, etc.)"
  - "Prioritized by frequency - most common unmapped markets first"

patterns-established:
  - "Audit script pattern for comprehensive mapping analysis"
  - "Category inference from market description/ID"

issues-created: []

# Metrics
duration: 15min
completed: 2026-02-02
---

# Phase 43 Plan 01: Market Mapping Audit Summary

**Comprehensive audit of market mapping across BetPawa, SportyBet, and Bet9ja identifying 380 unique unmapped market types with prioritized fix recommendations**

## Performance

- **Duration:** 15 min
- **Started:** 2026-02-02T14:15:00Z
- **Completed:** 2026-02-02T14:30:00Z
- **Tasks:** 3/3
- **Files created:** 3

## Accomplishments

- Created comprehensive audit script (`src/scripts/audit_market_mapping.py`)
- Analyzed 100 events across 46 tournaments and 32 countries
- Tested mapping for 17,605 SportyBet markets and 15,465 Bet9ja markets
- Identified 380 unique unmapped market types
- Generated categorized AUDIT-FINDINGS.md with prioritized recommendations

## Audit Statistics

### Platform Coverage

| Platform | Total Markets | Mapped | Failed | Success Rate |
|----------|--------------|--------|--------|--------------|
| SportyBet | 17,605 | 8,323 | 9,282 | 47.3% |
| Bet9ja | 15,465 | 5,580 | 9,885 | 36.1% |
| BetPawa (reference) | 5,039 | - | - | - |

### Error Breakdown

| Error Code | SportyBet | Bet9ja |
|------------|-----------|--------|
| UNKNOWN_MARKET | 8,305 | 8,553 |
| UNKNOWN_PARAM_MARKET | 834 | 690 |
| NO_MATCHING_OUTCOMES | 128 | 615 |
| UNSUPPORTED_PLATFORM | 15 | 27 |

### Top Unmapped Categories

1. **Uncategorized** - 3,447 occurrences (OUA, CHANCEMIXOU, etc.)
2. **Match Result** - 3,257 occurrences (1X2OU, 900069, etc.)
3. **Goals** - 2,770 occurrences (Goal Bounds, Excluded Goals, etc.)
4. **Half-Based** - 2,161 occurrences (HTFTOU, HTS, etc.)
5. **Over/Under** - 2,010 occurrences (547, 60180, etc.)

## Task Commits

1. **Task 1-2: Audit script** - `e557337`
2. **Task 3: Audit findings report** - `b3e54f8`

## Key Findings

### High Priority Gaps

1. **OUA (Bet9ja)** - 956 occurrences - Away Over/Under variant
2. **Player Bookings (SportyBet)** - 583 occurrences - Player to be booked market
3. **1X2OU (Bet9ja)** - 348 occurrences - 1X2 + Over/Under combo
4. **DCOU (Bet9ja)** - 342 occurrences - Double Chance + Over/Under combo
5. **900069 (SportyBet)** - 312 occurrences - 1X2 from 1-5 minutes

### Error Pattern Analysis

- **UNKNOWN_MARKET (16,858 total)**: Markets exist on competitor platforms but have no mapping definition
- **UNKNOWN_PARAM_MARKET (1,524 total)**: Parameterized markets where we have the base mapping but not param handling
- **NO_MATCHING_OUTCOMES (743 total)**: Mapping exists but outcome structure doesn't match
- **UNSUPPORTED_PLATFORM (42 total)**: Market exists but BetPawa doesn't offer it

## Recommended Next Phases

### Phase 44: High-Priority Market Mappings
Focus on top 20 markets by frequency:
- OUA, 1X2OU, DCOU (Bet9ja combo markets)
- Player Bookings (800117)
- Time-based 1X2 variants (900069, 60200, 60100)

### Phase 45: Outcome Structure Fixes
Address NO_MATCHING_OUTCOMES errors:
- HTFTOU, Multiscores, HTFTCS outcome mismatches
- TMGHO/TMGAW multigoal outcome mappings

### Phase 46: Extended Market Coverage
Lower priority markets (Cards, Corners, Player Props)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - audit completed successfully.

## Next Phase Readiness

- AUDIT-FINDINGS.md provides exact market IDs and priorities for Phase 44+
- audit_raw_data.json available for programmatic analysis
- Ready for `/gsd:plan-phase 44` with focused scope on high-priority gaps

---

*Phase: 43-market-mapping-audit*
*Completed: 2026-02-02*
