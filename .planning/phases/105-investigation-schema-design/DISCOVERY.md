# Phase 105: Investigation & Schema Design

## Current Write Path

The write path flows from scraping through change detection to database persistence:

```
┌─────────────────────────┐
│ EventCoordinator        │
│ scrape_batch()          │
└───────────┬─────────────┘
            │ raw API data per platform
            ▼
┌─────────────────────────┐
│ store_batch_results()   │  ← event_coordinator.py:1207
│ - _parse_betpawa_markets│
│ - _parse_sportybet_markets
│ - _parse_bet9ja_markets │
└───────────┬─────────────┘
            │ MarketOdds ORM objects + metadata
            ▼
┌─────────────────────────┐
│ Build SnapshotWriteData │  ← event_coordinator.py:1480-1532
│ - MarketWriteData tuples│
│ - Frozen dataclasses    │
└───────────┬─────────────┘
            │ DTOs (no ORM dependency)
            ▼
┌─────────────────────────┐
│ classify_batch_changes()│  ← change_detection.py:116
│ - Compare vs OddsCache  │
│ - Snapshot-level compare│
└───────────┬─────────────┘
            │ changed[] vs unchanged_ids[]
            ▼
┌─────────────────────────┐
│ OddsCache update        │  ← event_coordinator.py:1614-1687
│ - put_betpawa_snapshot()│
│ - put_competitor_snapshot()
│ - ALL data (not just changed)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ AsyncWriteQueue.enqueue()│ ← event_coordinator.py:1700-1730
│ - WriteBatch with:      │
│   - changed_betpawa[]   │
│   - unchanged_bp_ids[]  │
└───────────┬─────────────┘
            │ background task
            ▼
┌─────────────────────────┐
│ handle_write_batch()    │  ← write_handler.py:89
│ - INSERT OddsSnapshot   │
│ - flush() for IDs       │
│ - INSERT all MarketOdds │
│ - UPDATE last_confirmed │
│ - commit()              │
└─────────────────────────┘
```

### Key Code References

| Function | File:Line | Purpose |
|----------|-----------|---------|
| `store_batch_results()` | event_coordinator.py:1207 | Main orchestrator for batch storage |
| `classify_batch_changes()` | change_detection.py:116 | Snapshot-level change detection |
| `markets_changed()` | change_detection.py:49 | Compare cached vs new markets |
| `handle_write_batch()` | write_handler.py:89 | Actual DB INSERT/UPDATE operations |
| `_build_market_odds()` | write_handler.py:55 | Convert DTO to ORM model |

### Data Structures

**SnapshotWriteData** (write_queue.py:59):
```python
@dataclass(frozen=True)
class SnapshotWriteData:
    event_id: int
    bookmaker_id: int
    scrape_run_id: int | None
    markets: tuple[MarketWriteData, ...]  # ALL markets
```

**WriteBatch** (write_queue.py:92):
```python
@dataclass(frozen=True)
class WriteBatch:
    changed_betpawa: tuple[SnapshotWriteData, ...]  # Full snapshots
    changed_competitor: tuple[CompetitorSnapshotWriteData, ...]
    unchanged_betpawa_ids: tuple[int, ...]  # Just IDs for UPDATE
    unchanged_competitor_ids: tuple[int, ...]
```

### Change Detection Algorithm

The current algorithm (change_detection.py:49-113):

1. **Normalize outcomes** by sorting on (name, odds, is_active)
2. **Build lookup** by (betpawa_market_id, line) for cached markets
3. **Compare each new market** against cached version
4. **Any difference = entire snapshot changed** (writes ALL markets)

**Critical Problem:**
```
IF markets_changed(cached_markets, new_markets):
    # ALL 50+ markets get INSERT'd as new rows
    # Even if only 1 market's odds changed
```

### Current Database Schema

**odds_snapshots** (odds.py:26):
- id (BigInteger PK)
- event_id (FK events)
- bookmaker_id (FK bookmakers)
- captured_at (timestamp)
- last_confirmed_at (timestamp)

**market_odds** (odds.py:85):
- id (BigInteger PK)
- snapshot_id (FK odds_snapshots)
- betpawa_market_id (VARCHAR 50)
- betpawa_market_name (VARCHAR 255)
- line (FLOAT nullable)
- outcomes (JSONB)
- market_groups (JSONB)
- unavailable_at (TIMESTAMP nullable)

**Relationship:** One snapshot → Many market_odds (cascade delete)

---

## Current Read Paths

### Events List API

**Endpoint:** `GET /api/events` (events.py:1143)

**Query Pattern - Cache First:**
```python
# events.py:63-118
async def _load_snapshots_cached(event_ids, cache, db):
    # 1. Try cache first
    betpawa = cache.get_betpawa_snapshots(event_ids)
    competitor = cache.get_competitor_snapshots(event_ids)

    # 2. DB fallback for misses
    bp_miss_ids = [eid for eid in event_ids if eid not in cached_bp_ids]
    if bp_miss_ids:
        db_betpawa = await _load_latest_snapshots_for_events(db, bp_miss_ids)
```

**DB Query for Misses** (events.py:254-307):
```sql
-- Subquery: latest snapshot ID per (event_id, bookmaker_id)
SELECT event_id, bookmaker_id, MAX(id) as max_id
FROM odds_snapshots
WHERE event_id IN (...)
GROUP BY event_id, bookmaker_id

-- Main query: fetch snapshots + eager load markets
SELECT odds_snapshots.*, market_odds.*
FROM odds_snapshots
JOIN (...subquery...) ON ids match
-- Uses selectinload(OddsSnapshot.markets)
```

**Fields Used in Response:**
- market.betpawa_market_id (filter for INLINE_MARKET_IDS)
- market.betpawa_market_name
- market.line (filter for line=2.5 on Over/Under)
- market.outcomes (parse for OutcomeOdds)
- market.unavailable_at (availability state)

### Event Detail API

**Endpoint:** `GET /api/events/{event_id}` (events.py:1021)

Same pattern as events list but returns ALL markets (not just inline).

**Additional Fields Used:**
- market.market_groups (for tabbed navigation)
- All handicap fields (handicap_type, handicap_home, handicap_away)

### History API

**Odds History** (history.py:195):
```sql
SELECT odds_snapshots.*, market_odds.*
FROM odds_snapshots
JOIN market_odds ON market_odds.snapshot_id = odds_snapshots.id
WHERE odds_snapshots.event_id = :event_id
  AND odds_snapshots.bookmaker_id = :bookmaker_id
  AND market_odds.betpawa_market_id = :market_id
  AND market_odds.line = :line  -- optional specifier
  AND odds_snapshots.captured_at BETWEEN :from_time AND :to_time
ORDER BY odds_snapshots.captured_at ASC
```

**Fields Used:**
- snapshot.captured_at (X-axis timestamp)
- market.outcomes (Y-axis odds values)
- market.unavailable_at (availability indicator)

**Margin History** (history.py:363):
Same query pattern, but only returns margin (calculated from outcomes) + timestamps.

### Cache Structure

**CachedSnapshot** (odds_cache.py:78):
```python
@dataclass(frozen=True)
class CachedSnapshot:
    snapshot_id: int
    event_id: int
    bookmaker_id: int
    captured_at: datetime
    last_confirmed_at: datetime
    markets: tuple[CachedMarket, ...]
```

**CachedMarket** (odds_cache.py:46):
```python
@dataclass(frozen=True)
class CachedMarket:
    betpawa_market_id: str
    betpawa_market_name: str
    line: float | None
    handicap_type: str | None
    handicap_home: float | None
    handicap_away: float | None
    outcomes: list[dict]
    market_groups: list[str] | None
    unavailable_at: datetime | None
```

**Cache Layout:**
```
_betpawa_snapshots: Dict[event_id, Dict[bookmaker_id, CachedSnapshot]]
_competitor_snapshots: Dict[event_id, Dict[source, CachedSnapshot]]
```

---

## New Schema Design

### Design Goals

1. **Market-level change detection** - Only write markets that actually changed
2. **Current state table** - UPSERT pattern for latest odds (API reads)
3. **History table** - Append-only for changed markets (history charts)
4. **Unified storage** - Single table structure for BetPawa + competitors

### New Tables

#### market_odds_current (upsert pattern - latest odds)

```sql
CREATE TABLE market_odds_current (
    id BIGSERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,  -- BetPawa event ID (or negative for competitor-only)
    bookmaker_slug VARCHAR(20) NOT NULL,  -- 'betpawa', 'sportybet', 'bet9ja'
    betpawa_market_id VARCHAR(50) NOT NULL,
    betpawa_market_name VARCHAR(255) NOT NULL,
    line FLOAT,
    handicap_type VARCHAR(50),
    handicap_home FLOAT,
    handicap_away FLOAT,
    outcomes JSONB NOT NULL,
    market_groups JSONB,
    unavailable_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_confirmed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (event_id, bookmaker_slug, betpawa_market_id, COALESCE(line, 0))
);

-- Indexes for API queries
CREATE INDEX idx_moc_event ON market_odds_current(event_id);
CREATE INDEX idx_moc_bookmaker ON market_odds_current(bookmaker_slug);
CREATE INDEX idx_moc_market ON market_odds_current(betpawa_market_id);
CREATE INDEX idx_moc_event_bookmaker ON market_odds_current(event_id, bookmaker_slug);
```

**Key decisions:**
- **Unified BetPawa + competitor** in one table using bookmaker_slug
- **UNIQUE constraint** on (event_id, bookmaker_slug, market_id, line) enables UPSERT
- **COALESCE(line, 0)** handles NULL line values in unique constraint
- **last_confirmed_at** updated every scrape (even if unchanged)
- **last_updated_at** only updated when odds actually change

#### market_odds_history (append-only - when odds change)

```sql
CREATE TABLE market_odds_history (
    id BIGSERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL,
    bookmaker_slug VARCHAR(20) NOT NULL,
    betpawa_market_id VARCHAR(50) NOT NULL,
    line FLOAT,
    outcomes JSONB NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (captured_at);

-- Create partitions (monthly)
CREATE TABLE market_odds_history_2026_02 PARTITION OF market_odds_history
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE market_odds_history_2026_03 PARTITION OF market_odds_history
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
-- ... etc

-- Indexes for history queries
CREATE INDEX idx_moh_event_market_time
    ON market_odds_history(event_id, betpawa_market_id, captured_at DESC);
CREATE INDEX idx_moh_bookmaker_market
    ON market_odds_history(bookmaker_slug, betpawa_market_id);
```

**Key decisions:**
- **Append-only** - never update, just INSERT new rows when odds change
- **No FK to events** - allows storing competitor-only events
- **Monthly partitioning** - efficient time-range queries and retention cleanup
- **Minimal columns** - only what's needed for history charts (no handicap fields)

### Storage Estimates

**Current architecture:**
- ~50 markets × 500 events × 288 scrapes/day = **7.2M rows/day** in market_odds
- ~500 events × 288 scrapes/day = **144K rows/day** in odds_snapshots

**New architecture:**
- market_odds_current: ~50 markets × 500 events × 3 bookmakers = **75K rows total** (upsert, not growing)
- market_odds_history: ~5% change rate × 7.2M = **360K rows/day**

**Reduction: 95%** (7.2M → 360K rows/day for history)

### Impact Analysis

#### Tables to KEEP (no changes)
- events
- competitor_events
- bookmakers
- tournaments
- competitor_tournaments
- scrape_runs
- event_scrape_status
- settings

#### Tables to MIGRATE
- odds_snapshots → DELETE (data migrated to market_odds_current/history)
- market_odds → DELETE (data migrated to market_odds_current/history)
- competitor_odds_snapshots → DELETE
- competitor_market_odds → DELETE

#### Code Changes Required

**Write Path (Phase 106-107):**
1. `change_detection.py` - Market-level comparison instead of snapshot-level
2. `write_queue.py` - New DTOs for market-level writes
3. `write_handler.py` - UPSERT for current, INSERT for history
4. `event_coordinator.py` - Updated store_batch_results()

**Read Path (Phase 108):**
1. `events.py` - Query market_odds_current instead of join through snapshots
2. `history.py` - Query market_odds_history directly
3. `odds_cache.py` - Cache structure may simplify (no snapshot_id needed)

**Cache (Phase 107-108):**
1. `warmup.py` - Load from market_odds_current on startup
2. `odds_cache.py` - Remove snapshot_id from CachedSnapshot

### Migration Strategy

**Phase 106: Schema Migration**
1. Create new tables (market_odds_current, market_odds_history)
2. Migrate existing data (for history completeness)
3. Keep old tables temporarily for rollback

**Phase 107: Write Path Migration**
1. Update write handler to write to new tables
2. Dual-write period for validation
3. Remove old table writes

**Phase 108: Read Path Migration**
1. Update API queries to use new tables
2. Update cache warmup
3. Verify all endpoints work

**Phase 109: Cleanup**
1. Drop old tables (odds_snapshots, market_odds, competitor_*)
2. VACUUM FULL to reclaim space

---

## Key Findings Summary

### Root Cause of Storage Growth
The current snapshot-level change detection writes ALL markets whenever ANY market changes. With ~50 markets per event and ~5% typical change rate, we're writing 20x more data than necessary.

### Solution
Market-level change detection with:
1. **Upsert table** for current state (API reads) - fixed size, ~75K rows
2. **Append table** for history (charts) - only changed markets, 95% reduction

### Migration Complexity: MEDIUM
- Schema changes are straightforward
- Code changes span multiple files but are mechanical
- Data migration can run incrementally
- Rollback path available via temporary dual tables
