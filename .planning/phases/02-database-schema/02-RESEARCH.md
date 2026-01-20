# Phase 2: Database Schema - Research

**Researched:** 2026-01-20
**Domain:** PostgreSQL schema design for time-series odds snapshots
**Confidence:** HIGH

<research_summary>
## Summary

Researched PostgreSQL ecosystem for storing event-centric odds data with historical snapshots. The standard approach uses SQLAlchemy 2.0 async with asyncpg driver, Alembic for migrations, and native PostgreSQL partitioning (via pg_partman) for 30-day retention.

Key finding: **Skip TimescaleDB**. For 30-day retention with moderate write volume (snapshots every few minutes, 3 bookmakers, ~100 events), standard PostgreSQL with daily partitioning handles this easily. TimescaleDB adds operational complexity without meaningful benefit at this scale. TimescaleDB shines at 50M+ rows with continuous high-velocity inserts — not our use case.

**Primary recommendation:** Standard PostgreSQL with daily-partitioned snapshot tables, B-tree indexes on foreign keys, BRIN index on timestamp column for range queries. Use normalized tables for core entities (events, markets, odds), JSONB only for bookmaker-specific raw API responses.

</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | Async ORM + core | Modern async support, type hints, mature ecosystem |
| asyncpg | 0.29+ | PostgreSQL driver | Fastest async PostgreSQL driver, native protocol |
| Alembic | 1.13+ | Migrations | Official SQLAlchemy migration tool |
| Pydantic | 2.0+ | Validation | Already using for Phase 1 models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pg_partman | 5.0+ | Partition management | Automates daily partition creation/cleanup |
| psycopg | 3.1+ | Sync driver (Alembic) | Alembic migrations can use sync driver |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Standard PostgreSQL | TimescaleDB | TimescaleDB better at 50M+ rows, overkill for 30-day retention |
| SQLAlchemy | encode/databases | databases is lighter but SQLAlchemy has better ecosystem |
| pg_partman | Manual partitioning | pg_partman automates retention, worth the extension |
| asyncpg | psycopg3 async | asyncpg slightly faster, psycopg3 more feature-complete |

**Installation:**
```bash
pip install "sqlalchemy[asyncio]>=2.0.0" asyncpg>=0.29.0 alembic>=1.13.0
```

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── db/
│   ├── __init__.py
│   ├── engine.py          # Async engine + session factory
│   ├── base.py            # DeclarativeBase with naming conventions
│   └── models/
│       ├── __init__.py
│       ├── sport.py       # Sport, Tournament models
│       ├── event.py       # Event, EventBookmaker models
│       ├── odds.py        # OddsSnapshot, MarketOdds models
│       ├── bookmaker.py   # Bookmaker config model
│       └── scrape.py      # ScrapeRun, ScrapeError models
├── alembic/
│   ├── env.py             # Async migration config
│   └── versions/          # Migration files
└── alembic.ini
```

### Pattern 1: Async Engine + Session Factory
**What:** Single async engine per process, session factory for request-scoped sessions
**When to use:** All FastAPI applications with SQLAlchemy 2.0

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Create once at startup
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,  # CRITICAL for async
    class_=AsyncSession,
)

# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
```

### Pattern 2: Event-Centric Schema with Snapshot History
**What:** Events as primary entity, odds stored per-snapshot with timestamp
**When to use:** Any odds comparison requiring historical analysis

```
┌─────────────────┐
│     Sport       │
└────────┬────────┘
         │
┌────────▼────────┐
│   Tournament    │
└────────┬────────┘
         │
┌────────▼────────┐      ┌─────────────────┐
│     Event       │◄────►│  EventBookmaker │ (SportRadar ID per bookmaker)
└────────┬────────┘      └─────────────────┘
         │
┌────────▼────────┐
│  OddsSnapshot   │  (partitioned by captured_at)
└────────┬────────┘
         │
┌────────▼────────┐
│   MarketOdds    │  (individual market odds per snapshot)
└─────────────────┘
```

### Pattern 3: Daily Partitioning for Retention
**What:** Partition snapshots by day, drop partitions older than 30 days
**When to use:** Time-based retention requirements

```sql
-- Parent table (partitioned)
CREATE TABLE odds_snapshots (
    id BIGSERIAL,
    event_id INTEGER NOT NULL,
    bookmaker_id INTEGER NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    raw_response JSONB,
    PRIMARY KEY (id, captured_at)
) PARTITION BY RANGE (captured_at);

-- pg_partman handles partition creation/cleanup
SELECT partman.create_parent(
    'public.odds_snapshots',
    'captured_at',
    'native',
    'daily'
);

-- Retention: 30 days
UPDATE partman.part_config
SET retention = '30 days', retention_keep_table = false
WHERE parent_table = 'public.odds_snapshots';
```

### Pattern 4: Naming Conventions for Alembic
**What:** Explicit constraint naming for reliable autogenerate
**When to use:** Always — prevents Alembic migration issues

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)
```

### Anti-Patterns to Avoid
- **Lazy loading in async:** Causes implicit I/O errors. Use `selectinload()` or `joinedload()` explicitly.
- **Shared AsyncSession across tasks:** One session per request/task. Sessions are not thread-safe.
- **JSONB for everything:** Use normalized tables for core entities, JSONB only for raw API responses.
- **Missing `expire_on_commit=False`:** Required for async sessions to avoid post-commit attribute errors.

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Partition management | Manual CREATE/DROP partition scripts | pg_partman extension | Handles pre-creation, retention, edge cases |
| Connection pooling | Custom pool logic | SQLAlchemy pool settings | Battle-tested, handles edge cases |
| Migration tracking | Custom version table | Alembic | Industry standard, handles branches |
| Async session lifecycle | Manual session open/close | `async_sessionmaker` context | Handles cleanup, errors, transactions |
| Constraint naming | Default PostgreSQL names | SQLAlchemy naming convention | Enables reliable Alembic autogenerate |

**Key insight:** PostgreSQL and SQLAlchemy have decades of refinement. Custom solutions for connection pooling, partitioning, or migrations will have bugs that the standard tools solved years ago.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Lazy Loading in Async Context
**What goes wrong:** `MissingGreenlet` error when accessing relationship attributes
**Why it happens:** SQLAlchemy tries implicit I/O which is forbidden in async
**How to avoid:** Always use eager loading: `selectinload()`, `joinedload()`, or `subqueryload()`
**Warning signs:** Errors mentioning "greenlet" or "implicit IO"

### Pitfall 2: Using Sync Alembic with Async Engine
**What goes wrong:** Import errors or connection issues during migrations
**Why it happens:** Mixing async engine URL with sync Alembic env.py
**How to avoid:** Either use `engine.sync_engine` in Alembic, or configure full async `env.py` with `run_sync()`
**Warning signs:** "Cannot use asyncpg driver" errors in Alembic

### Pitfall 3: Missing Indexes on Partitioned Tables
**What goes wrong:** Slow queries even with indexes defined on parent
**Why it happens:** Indexes must be created on each partition (though PostgreSQL 11+ auto-propagates)
**How to avoid:** Verify indexes exist on partitions: `\di+ <table_name>*`
**Warning signs:** Sequential scans on partitioned tables in `EXPLAIN ANALYZE`

### Pitfall 4: BRIN Index on Non-Correlated Data
**What goes wrong:** BRIN index provides no speedup, falls back to seq scan
**Why it happens:** BRIN requires physical storage order to correlate with column values
**How to avoid:** Use BRIN only for `captured_at` timestamp (naturally sequential), use B-tree for IDs
**Warning signs:** BRIN index scans that don't prune blocks

### Pitfall 5: Large JSONB Documents
**What goes wrong:** Slow reads, TOAST overhead, document bloat
**Why it happens:** PostgreSQL TOASTs JSONB >2KB, repeated key strings aren't deduplicated
**How to avoid:** Keep JSONB for raw responses only, normalize frequently-queried fields to columns
**Warning signs:** JSONB columns >10KB average, queries accessing nested JSONB fields frequently

### Pitfall 6: Not Disposing Async Engine
**What goes wrong:** "Event loop is closed" warnings on shutdown
**Why it happens:** Async connections not properly closed
**How to avoid:** Call `await engine.dispose()` in FastAPI shutdown event
**Warning signs:** RuntimeError warnings about event loops on app shutdown

</common_pitfalls>

<code_examples>
## Code Examples

### Async Engine Setup (FastAPI)
```python
# Source: SQLAlchemy 2.0 asyncio docs
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/betpawa",
    pool_size=10,
    max_overflow=20,
    echo=False,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()  # Clean shutdown

app = FastAPI(lifespan=lifespan)
```

### Model with Eager Loading
```python
# Source: SQLAlchemy 2.0 ORM docs
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))
    name: Mapped[str]
    kickoff: Mapped[datetime]

    # Relationships
    tournament: Mapped["Tournament"] = relationship(back_populates="events")
    snapshots: Mapped[list["OddsSnapshot"]] = relationship(back_populates="event")

# Query with eager loading
async with async_session_factory() as session:
    stmt = (
        select(Event)
        .options(selectinload(Event.snapshots))
        .where(Event.id == event_id)
    )
    result = await session.execute(stmt)
    event = result.scalar_one()
```

### Alembic Async env.py
```python
# Source: Alembic cookbook + community patterns
import asyncio
from sqlalchemy.ext.asyncio import async_engine_from_config

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())
```

### Partitioned Table with Indexes
```sql
-- Source: PostgreSQL + pg_partman docs
CREATE TABLE odds_snapshots (
    id BIGSERIAL,
    event_id INTEGER NOT NULL REFERENCES events(id),
    bookmaker_id INTEGER NOT NULL REFERENCES bookmakers(id),
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, captured_at)
) PARTITION BY RANGE (captured_at);

-- B-tree for FK lookups (auto-propagates to partitions)
CREATE INDEX idx_snapshots_event ON odds_snapshots (event_id);
CREATE INDEX idx_snapshots_bookmaker ON odds_snapshots (bookmaker_id);

-- BRIN for time-range queries (data is naturally time-ordered)
CREATE INDEX idx_snapshots_captured_brin ON odds_snapshots
    USING BRIN (captured_at) WITH (pages_per_range = 32);

-- Composite for common query pattern
CREATE INDEX idx_snapshots_event_time ON odds_snapshots (event_id, captured_at DESC);
```

</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.4 with `future=True` | SQLAlchemy 2.0 native | 2023 | Cleaner async API, better typing |
| psycopg2 for async via greenlet | asyncpg or psycopg3 native async | 2022+ | Better performance, simpler code |
| Manual partitioning | pg_partman | Stable since PostgreSQL 10+ | Automation, reliability |
| `declarative_base()` | `DeclarativeBase` class | SQLAlchemy 2.0 | Better typing, cleaner |

**New tools/patterns to consider:**
- **PostgreSQL 15+ MERGE statement:** Useful for upsert patterns (INSERT ON CONFLICT alternative)
- **asyncpg connection pooling:** Built-in pooling can complement SQLAlchemy's pool

**Deprecated/outdated:**
- **SQLAlchemy `session.query()`:** Use `select()` statement instead
- **`autocommit=True`:** Removed in SQLAlchemy 2.0, use explicit `begin()` blocks
- **psycopg2 with asyncio:** Use asyncpg or psycopg3 instead

</sota_updates>

<open_questions>
## Open Questions

1. **pg_partman installation in cloud environments**
   - What we know: pg_partman is available in AWS RDS, Azure, most managed PostgreSQL
   - What's unclear: Specific cloud provider setup may vary
   - Recommendation: Verify pg_partman availability in target deployment environment during Phase 3

2. **Exact partition granularity**
   - What we know: Daily partitions recommended for 30-day retention
   - What's unclear: Actual snapshot volume might warrant different granularity
   - Recommendation: Start with daily, monitor partition sizes, adjust if needed

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Async Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) - Engine setup, session patterns, gotchas
- [PostgreSQL 18 Index Types](https://www.postgresql.org/docs/current/indexes-types.html) - B-tree, BRIN characteristics
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) - Async migrations, naming conventions

### Secondary (MEDIUM confidence)
- [Crunchy Data: pg_partman](https://www.crunchydata.com/blog/auto-archiving-and-data-retention-management-in-postgres-with-pg_partman) - Partition retention patterns
- [Crunchy Data: When Does BRIN Win](https://www.crunchydata.com/blog/postgres-indexing-when-does-brin-win) - BRIN vs B-tree decision guidance
- [TimescaleDB vs PostgreSQL](https://www.timescale.com/blog/timescaledb-vs-6a696248104e/) - When TimescaleDB is worth it
- [Heap: When to Avoid JSONB](https://www.heap.io/blog/when-to-avoid-jsonb-in-a-postgresql-schema) - JSONB performance pitfalls

### Tertiary (LOW confidence - validated patterns)
- [FastAPI + SQLAlchemy 2.0 Setup](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/) - Integration patterns
- [10 SQLAlchemy 2.0 Patterns](https://medium.com/@ThinkingLoop/10-sqlalchemy-2-0-patterns-for-clean-async-postgres-af8c4bcd86fe) - Community best practices

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: PostgreSQL + SQLAlchemy 2.0 async
- Ecosystem: asyncpg, Alembic, pg_partman
- Patterns: Event-centric schema, daily partitioning, eager loading
- Pitfalls: Async gotchas, indexing, JSONB misuse

**Confidence breakdown:**
- Standard stack: HIGH - Official docs, mature ecosystem
- Architecture: HIGH - Well-established patterns, official examples
- Pitfalls: HIGH - Documented in official sources and community
- Code examples: HIGH - From official documentation

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - stable ecosystem)

</metadata>

---

*Phase: 02-database-schema*
*Research completed: 2026-01-20*
*Ready for planning: yes*
