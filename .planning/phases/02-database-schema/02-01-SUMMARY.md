---
phase: 02-database-schema
plan: 01
subsystem: database
tags: [sqlalchemy, asyncpg, postgresql, async]

requires:
  - phase: 01-market-mapping-port
    provides: market types and patterns for odds data storage

provides:
  - SQLAlchemy 2.0 async engine with asyncpg driver
  - Session factory with expire_on_commit=False for async safety
  - FastAPI dependency injection pattern (get_db)
  - 5 core models: Sport, Tournament, Bookmaker, Event, EventBookmaker
  - Naming conventions for Alembic autogenerate

affects: [scraper-integration, event-matching, api-endpoints]

tech-stack:
  added: [sqlalchemy>=2.0.0, asyncpg>=0.29.0]
  patterns: [DeclarativeBase class, Mapped[] type hints, mapped_column()]

key-files:
  created:
    - src/db/__init__.py
    - src/db/base.py
    - src/db/engine.py
    - src/db/models/__init__.py
    - src/db/models/sport.py
    - src/db/models/bookmaker.py
    - src/db/models/event.py
  modified:
    - src/pyproject.toml

key-decisions:
  - "Use module-level engine creation (standard FastAPI pattern, not lazy)"
  - "expire_on_commit=False for async sessions (critical for detached object access)"
  - "Naming conventions in MetaData for Alembic autogenerate support"
  - "sportradar_id as cross-platform matching key"

patterns-established:
  - "DeclarativeBase with MetaData(naming_convention=convention)"
  - "Mapped[] + mapped_column() for all columns"
  - "back_populates for bidirectional relationships"
  - "UniqueConstraint for composite uniqueness (event_id, bookmaker_id)"

issues-created: []

duration: 5 min
completed: 2026-01-20
---

# Phase 2 Plan 01: Database Foundation Summary

**SQLAlchemy 2.0 async engine with asyncpg, session factory, and 5 core models (Sport, Tournament, Bookmaker, Event, EventBookmaker)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-20T11:31:17Z
- **Completed:** 2026-01-20T11:36:07Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Async database engine with connection pooling (10 + 20 overflow)
- Session factory with `expire_on_commit=False` (critical for async)
- FastAPI dependency injection via `get_db()` async generator
- Sport/Tournament hierarchy with optional sportradar_id
- Event model with sportradar_id as cross-platform matching key
- EventBookmaker junction table with unique constraint on (event_id, bookmaker_id)
- Naming conventions for all constraints (Alembic autogenerate ready)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create async engine and session factory** - `5d24e13` (feat)
2. **Task 2: Create core entity models** - `5944162` (feat)

**Plan metadata:** (pending this commit)

## Files Created/Modified

- `src/db/__init__.py` - Package exports: Base, engine, async_session_factory, get_db, dispose_engine
- `src/db/base.py` - DeclarativeBase with naming conventions for Alembic
- `src/db/engine.py` - Async engine, session factory, FastAPI dependency
- `src/db/models/__init__.py` - Model exports
- `src/db/models/sport.py` - Sport and Tournament models
- `src/db/models/bookmaker.py` - Bookmaker configuration model
- `src/db/models/event.py` - Event and EventBookmaker models
- `src/pyproject.toml` - Added SQLAlchemy and asyncpg dependencies

## Decisions Made

- **Module-level engine creation** - Standard FastAPI pattern, creates engine at import time rather than lazy initialization
- **expire_on_commit=False** - Critical for async sessions to avoid DetachedInstanceError when accessing objects after commit
- **Naming conventions in MetaData** - Enables reliable Alembic autogenerate for migrations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing database dependencies**
- **Found during:** Task 1 (engine creation)
- **Issue:** SQLAlchemy and asyncpg not in pyproject.toml
- **Fix:** Added `sqlalchemy[asyncio]>=2.0.0` and `asyncpg>=0.29.0` to dependencies
- **Files modified:** src/pyproject.toml
- **Verification:** Imports succeed
- **Committed in:** 5d24e13 (Task 1 commit)

**2. [Rule 3 - Blocking] Fixed package discovery**
- **Found during:** Task 1 (import verification)
- **Issue:** Multiple top-level packages error in setuptools
- **Fix:** Updated pyproject.toml to use `[tool.setuptools.packages.find]` with explicit includes
- **Files modified:** src/pyproject.toml
- **Verification:** Package imports work correctly
- **Committed in:** 5d24e13 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (both blocking issues), 0 deferred
**Impact on plan:** Both fixes were essential for the database code to be importable. No scope creep.

## Issues Encountered

None.

## Next Phase Readiness

- Database foundation complete with async engine and core models
- Ready for Plan 02: Odds snapshot models (OddsSnapshot, MarketOdds, OutcomeOdds)
- Alembic migration setup can be added in a later plan if needed

---
*Phase: 02-database-schema*
*Completed: 2026-01-20*
