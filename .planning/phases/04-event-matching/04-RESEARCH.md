# Phase 4: Event Matching Service - Research

**Researched:** 2026-01-20
**Domain:** Cross-platform event matching and odds aggregation
**Confidence:** HIGH

<research_summary>
## Summary

Researched patterns for cross-platform event matching and odds aggregation in sports betting contexts. The key finding: this is a commodity database problem, not a complex entity resolution challenge.

Since all three bookmakers (SportyBet, BetPawa, Bet9ja) use SportRadar as their data provider, event matching is **deterministic by ID** — not probabilistic fuzzy matching. The existing schema already has `sportradar_id` as a unique constraint on the `events` table.

The main technical considerations are:
1. Efficient upsert patterns for SQLAlchemy 2.0 async
2. Handling the "Betpawa-first" metadata priority
3. Query patterns for filtering matched/unmatched events

**Primary recommendation:** Use PostgreSQL's `INSERT...ON CONFLICT DO UPDATE` via SQLAlchemy's dialect-specific `insert()` for upserts. Keep the matching logic simple — exact ID match only, no fuzzy matching libraries needed.

</research_summary>

<standard_stack>
## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0.x | ORM and query building | Already established, async support |
| asyncpg | 0.29.x | PostgreSQL async driver | Already in use, best performance |
| Pydantic | 2.x | Data validation | Already established for schemas |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI | 0.109.x | API framework | Already in use for endpoints |

### Not Needed
| Library | Purpose | Why Skip |
|---------|---------|----------|
| dedupe | Fuzzy matching | SportRadar IDs are exact — no fuzzy matching needed |
| Splink | Probabilistic record linkage | Same — deterministic matching by ID |
| recordlinkage | Entity resolution | Overkill for exact ID matching |

**Installation:** No new packages needed. Everything required is already in the project.

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── matching/
│   ├── __init__.py
│   ├── service.py          # EventMatchingService class
│   ├── schemas.py          # Pydantic models for matched events
│   └── queries.py          # Reusable query helpers (optional)
├── api/routes/
│   └── events.py           # API endpoints for matched events
```

### Pattern 1: Upsert-on-Scrape
**What:** Match events during scrape, not as a batch job
**When to use:** Every time events are scraped
**Example:**
```python
from sqlalchemy.dialects.postgresql import insert

async def upsert_event(
    db: AsyncSession,
    sportradar_id: str,
    tournament_id: int,
    name: str,
    home_team: str,
    away_team: str,
    kickoff: datetime,
) -> Event:
    """Insert or update event by SportRadar ID."""
    stmt = insert(Event).values(
        sportradar_id=sportradar_id,
        tournament_id=tournament_id,
        name=name,
        home_team=home_team,
        away_team=away_team,
        kickoff=kickoff,
    )

    # On conflict, update metadata (if from Betpawa)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sportradar_id"],
        set_={
            "name": stmt.excluded.name,
            "home_team": stmt.excluded.home_team,
            "away_team": stmt.excluded.away_team,
            "kickoff": stmt.excluded.kickoff,
        },
    ).returning(Event)

    result = await db.execute(stmt)
    return result.scalar_one()
```

### Pattern 2: Betpawa-First Metadata Priority
**What:** Only update event metadata when data comes from Betpawa
**When to use:** When storing events from different platforms
**Example:**
```python
async def upsert_event_from_platform(
    db: AsyncSession,
    platform: Platform,
    event_data: dict,
) -> Event:
    """Upsert event with Betpawa-priority metadata."""

    if platform == Platform.BETPAWA:
        # Betpawa: Always update metadata
        return await upsert_event_with_metadata(db, event_data)
    else:
        # Competitors: Insert if new, but don't overwrite Betpawa metadata
        existing = await get_event_by_sportradar_id(db, event_data["sportradar_id"])
        if existing:
            # Event exists — just return it, don't update metadata
            return existing
        else:
            # New event not in Betpawa — store competitor metadata
            return await insert_event(db, event_data)
```

### Pattern 3: Efficient Bulk Upsert
**What:** Batch upserts for multiple events
**When to use:** Processing full scrape results
**Example:**
```python
async def bulk_upsert_events(
    db: AsyncSession,
    events: list[dict],
) -> list[int]:
    """Bulk upsert events, return IDs."""
    if not events:
        return []

    stmt = insert(Event).values(events)
    stmt = stmt.on_conflict_do_update(
        index_elements=["sportradar_id"],
        set_={
            "kickoff": stmt.excluded.kickoff,  # Always update kickoff time
        },
    ).returning(Event.id)

    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]
```

### Anti-Patterns to Avoid
- **Fuzzy matching:** Don't use string similarity for matching — SportRadar IDs are exact
- **Separate batch job:** Don't defer matching to a cron job — match during scrape
- **N+1 queries:** Don't fetch each event individually — use bulk operations
- **Ignoring partial matches:** Don't require all 3 platforms — 2-platform comparisons are valid

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Upsert logic | Manual SELECT then INSERT/UPDATE | `insert().on_conflict_do_update()` | Race conditions, extra round trips |
| Fuzzy matching | Levenshtein distance functions | Nothing — use exact ID | SportRadar IDs are deterministic |
| Bulk processing | Loop with individual inserts | Single multi-value INSERT | 10-100x performance difference |
| ID generation | UUID or sequence | Auto-increment with RETURNING | Simpler, PostgreSQL handles it |

**Key insight:** The matching problem is already solved by SportRadar providing universal IDs. The complexity is in the data flow (which platform's metadata wins), not in the matching algorithm.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Race Conditions in Upsert
**What goes wrong:** Two concurrent scrapes try to insert same event, one fails
**Why it happens:** Manual SELECT-then-INSERT pattern without proper locking
**How to avoid:** Use `INSERT...ON CONFLICT` — PostgreSQL handles atomicity
**Warning signs:** IntegrityError on unique constraint during high concurrency

### Pitfall 2: Overwriting Betpawa Metadata
**What goes wrong:** Competitor data overwrites Betpawa's canonical metadata
**Why it happens:** Unconditional UPDATE on conflict
**How to avoid:** Check source platform before updating; use conditional update logic
**Warning signs:** Event names changing unexpectedly between scrapes

### Pitfall 3: N+1 Query Pattern
**What goes wrong:** Fetching events one-by-one when processing scrape results
**Why it happens:** ORM convenience over performance
**How to avoid:** Bulk fetch by `sportradar_id IN (...)` then process in memory
**Warning signs:** Slow scrape processing, high database connection count

### Pitfall 4: Missing Tournament Context
**What goes wrong:** Events created without tournament linkage
**Why it happens:** Tournament not yet created when event arrives
**How to avoid:** Upsert tournament first (by SportRadar ID), then event with FK
**Warning signs:** Orphaned events, foreign key errors

### Pitfall 5: Stale Kickoff Times
**What goes wrong:** Event kickoff time is wrong
**Why it happens:** Not updating kickoff on subsequent scrapes
**How to avoid:** Always update `kickoff` field even for existing events
**Warning signs:** Events showing wrong times in UI

</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from SQLAlchemy 2.0 documentation and project conventions:

### PostgreSQL Upsert with Returning
```python
# Source: SQLAlchemy 2.0 PostgreSQL dialect docs
from sqlalchemy.dialects.postgresql import insert

stmt = insert(Event).values(
    sportradar_id="sr:match:12345",
    name="Team A vs Team B",
    tournament_id=1,
    home_team="Team A",
    away_team="Team B",
    kickoff=datetime(2026, 1, 25, 15, 0),
)

# Update specific fields on conflict
stmt = stmt.on_conflict_do_update(
    index_elements=["sportradar_id"],
    set_={
        "kickoff": stmt.excluded.kickoff,
        "name": stmt.excluded.name,
    },
).returning(Event.id, Event.sportradar_id)

result = await db.execute(stmt)
event_id, sr_id = result.one()
```

### Bulk Fetch by SportRadar IDs
```python
# Efficient lookup for multiple events
from sqlalchemy import select

async def get_events_by_sportradar_ids(
    db: AsyncSession,
    sportradar_ids: list[str],
) -> dict[str, Event]:
    """Fetch events by SportRadar IDs, return as dict for O(1) lookup."""
    stmt = select(Event).where(Event.sportradar_id.in_(sportradar_ids))
    result = await db.execute(stmt)
    events = result.scalars().all()
    return {e.sportradar_id: e for e in events}
```

### Platform-Aware Event Processing
```python
async def process_scraped_events(
    db: AsyncSession,
    platform: Platform,
    scraped_events: list[dict],
) -> ProcessingResult:
    """Process events from a single platform scrape."""

    # Extract SportRadar IDs
    sr_ids = [e["sportradar_id"] for e in scraped_events]

    # Bulk fetch existing events
    existing = await get_events_by_sportradar_ids(db, sr_ids)

    new_events = []
    updated_events = []

    for event_data in scraped_events:
        sr_id = event_data["sportradar_id"]

        if sr_id in existing:
            # Event exists — update only if Betpawa
            if platform == Platform.BETPAWA:
                await update_event_metadata(db, existing[sr_id], event_data)
                updated_events.append(sr_id)
        else:
            # New event — insert
            new_event = await insert_event(db, event_data, platform)
            new_events.append(new_event.id)

    await db.commit()
    return ProcessingResult(new=len(new_events), updated=len(updated_events))
```

</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `session.bulk_insert_mappings()` | `insert().values([...])` | SQLAlchemy 2.0 | Bulk methods now equally fast, simpler API |
| Manual SELECT + INSERT | `INSERT...ON CONFLICT` | PostgreSQL 9.5+ | Atomic upsert, no race conditions |
| Sync ORM | Async ORM with asyncpg | SQLAlchemy 1.4/2.0 | Better concurrency for I/O-bound operations |

**New tools/patterns to consider:**
- **Staging table approach:** For very large bulk upserts (10k+ rows), COPY to temp table then INSERT...SELECT with ON CONFLICT can be faster
- **SQLAlchemy 2.0 `insert().returning()`:** Returns inserted/updated rows in same statement

**Deprecated/outdated:**
- **`session.add()` loops:** Use bulk insert for multiple objects
- **Raw SQL for upserts:** SQLAlchemy's `insert().on_conflict_do_update()` is clean and safe

</sota_updates>

<open_questions>
## Open Questions

1. **Tournament handling**
   - What we know: Events link to tournaments via FK
   - What's unclear: How to handle tournament upsert when SportRadar ID might be missing
   - Recommendation: Upsert tournament by name+sport as fallback, prefer SportRadar ID

2. **Competitor metadata fallback**
   - What we know: Betpawa metadata is canonical; use competitor metadata when Betpawa missing
   - What's unclear: What if competitor metadata differs between SportyBet and Bet9ja?
   - Recommendation: First-in-wins for competitor metadata; don't overwrite between competitors

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 PostgreSQL Dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html) - INSERT...ON CONFLICT patterns
- [SQLAlchemy 2.0 ORM Bulk Operations](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html) - Bulk insert best practices
- Project codebase - Existing patterns in `src/db/models/` and `src/scraping/`

### Secondary (MEDIUM confidence)
- [SportsDataIO Aggregated Odds Guide](https://sportsdata.io/developers/aggregated-odds-guide) - Schema patterns for odds aggregation
- [CockroachDB Sports Betting Reference Architecture](https://www.cockroachlabs.com/blog/real-money-gaming-reference-architecture/) - ACID requirements for betting data

### Tertiary (LOW confidence - needs validation)
- [PostgreSQL Bulk Insert Optimization](https://risingwave.com/blog/top-techniques-to-enhance-upsert-speed-in-postgresql/) - Performance tips (WebSearch only, verify with benchmarks)

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: SQLAlchemy 2.0 async with PostgreSQL
- Ecosystem: No external libraries needed (existing stack sufficient)
- Patterns: Upsert, bulk operations, platform-priority metadata
- Pitfalls: Race conditions, N+1 queries, metadata overwrites

**Confidence breakdown:**
- Standard stack: HIGH - using existing project dependencies
- Architecture: HIGH - follows established project patterns
- Pitfalls: HIGH - well-documented database patterns
- Code examples: HIGH - from SQLAlchemy docs and project conventions

**Research date:** 2026-01-20
**Valid until:** 2026-03-20 (60 days - stable patterns)

</metadata>

---

*Phase: 04-event-matching*
*Research completed: 2026-01-20*
*Ready for planning: yes*
