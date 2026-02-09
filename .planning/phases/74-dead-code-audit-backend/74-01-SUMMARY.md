---
phase: 74-dead-code-audit-backend
plan: 01
subsystem: api, scraping
tags: [python, fastapi, dead-code, cleanup, tech-debt]

# Dependency graph
requires:
  - phase: 59-sse-removal
    provides: WebSocket-only architecture (removed SSE endpoints)
provides:
  - Cleaner backend codebase with dead code removed
  - Updated CONCERNS.md with remaining audit notes
affects: [75-dead-code-audit-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - src/scraping/broadcaster.py
    - src/api/dependencies.py
    - .planning/codebase/CONCERNS.md
  deleted:
    - src/scripts/audit_market_mapping.py
    - src/scripts/analyze_outcomes.py
    - src/scripts/verify_market_fixes.py

key-decisions:
  - "Removed 3 one-off v1.8 audit scripts that were no longer needed"
  - "Simplified dependencies.py to only re-export get_db (HTTP client dependencies were unused)"
  - "Deferred SSE docstring updates as LOW confidence cosmetic changes"

patterns-established: []

issues-created: []

# Metrics
duration: 12min
completed: 2026-02-09
---

# Phase 74 Plan 01: Backend Dead Code Audit Summary

**Removed 2 unused imports, 3 unused HTTP client dependency functions, and 3 one-off audit scripts (1,256 LOC deleted)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-09T14:00:00Z
- **Completed:** 2026-02-09T14:12:00Z
- **Tasks:** 3
- **Files modified:** 5 (2 modified, 3 deleted)

## Accomplishments
- Identified dead code via static analysis (Task 1)
- Removed confirmed HIGH CONFIDENCE dead code (Task 2)
- Updated CONCERNS.md with audit notes (Task 3)
- Verified application still imports correctly after cleanup

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Static analysis and dead code removal** - `7b71f52` (refactor)
2. **Task 3: Update CONCERNS.md** - `42e1e0d` (docs)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified

**Modified:**
- `src/scraping/broadcaster.py` - Removed unused `datetime` and `Platform` imports
- `src/api/dependencies.py` - Removed unused HTTP client dependency functions

**Deleted:**
- `src/scripts/audit_market_mapping.py` - One-off v1.8 market mapping audit script
- `src/scripts/analyze_outcomes.py` - One-off v1.8 outcome analysis script
- `src/scripts/verify_market_fixes.py` - One-off v1.8 market fix verification script

## Dead Code Removed

**HIGH CONFIDENCE (removed):**
| Category | Item | File | Lines |
|----------|------|------|-------|
| Unused imports | `datetime`, `Platform` | broadcaster.py | 2 |
| Unused functions | `get_sportybet_client()` | dependencies.py | ~12 |
| Unused functions | `get_betpawa_client()` | dependencies.py | ~12 |
| Unused functions | `get_bet9ja_client()` | dependencies.py | ~12 |
| Deprecated scripts | `audit_market_mapping.py` | src/scripts/ | 812 |
| Deprecated scripts | `analyze_outcomes.py` | src/scripts/ | 160 |
| Deprecated scripts | `verify_market_fixes.py` | src/scripts/ | 242 |

**Total LOC deleted:** 1,256

## Deferred for Review

**LOW CONFIDENCE (cosmetic, documented in CONCERNS.md):**
- SSE-related comments/docstrings in broadcaster.py, bridge.py, event_coordinator.py, jobs.py
- Recommendation: Update docstrings during next touch of these files

## Decisions Made

1. **Merged Task 1 and Task 2 commits** - Task 1 was analysis-only with no file changes, so combined with Task 2 for atomic commit
2. **Kept SSE docstring updates as LOW priority** - Functional code works correctly; docstring updates are cosmetic and can be done during future maintenance

## Deviations from Plan
None - plan executed exactly as written

## Issues Encountered
None

## Next Phase Readiness
- Ready for Phase 75: Dead Code Audit & Removal (Frontend)
- Backend codebase is cleaner with 1,256 LOC removed
- All remaining concerns documented in CONCERNS.md

---
*Phase: 74-dead-code-audit-backend*
*Completed: 2026-02-09*
