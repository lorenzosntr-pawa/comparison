# Phase 60: Investigation & Schema Design - DISCOVERY

## Current State Analysis

### SQL Diagnostics Summary (2026-02-06)

Analysis performed against production PostgreSQL database (localhost:5433/pawarisk) with ~4 days of data.

---

## 1. Snapshot Creation Pattern

### Key Finding: History IS Being Kept

**Query: Snapshots per event**
```sql
SELECT event_id, COUNT(*) as snapshot_count
FROM odds_snapshots
GROUP BY event_id
ORDER BY snapshot_count DESC
LIMIT 20;
```

**Results:**
| Event ID | Snapshot Count |
|----------|---------------|
| 2157     | 90            |
| 2158     | 90            |
| 2199     | 89            |
| ...      | 89            |

**Interpretation:**
- Events accumulate **52 snapshots on average** (median = 52)
- Maximum observed: **90 snapshots per event**
- Minimum: 1 snapshot (newly discovered events)
- **Current behavior: Multiple snapshots ARE kept per event (not overwritten)**

### last_confirmed_at Usage

**Query: Snapshots with confirmation timestamps**
```sql
SELECT
  COUNT(*) FILTER (WHERE last_confirmed_at IS NOT NULL) as confirmed,
  COUNT(*) FILTER (WHERE last_confirmed_at IS NULL) as never_confirmed,
  COUNT(*) as total
FROM odds_snapshots;
```

**Results:**
- Confirmed (unchanged during subsequent scrapes): **25,925** (28.7%)
- New or changed: **64,416** (71.3%)
- Total snapshots: **90,341**

**Interpretation:**
- **28.7% of snapshots** have `last_confirmed_at` set, meaning they were confirmed as unchanged during a subsequent scrape cycle
- The remaining 71.3% are either:
  - First scrapes for an event (no prior data to compare)
  - Actual odds changes (INSERT instead of UPDATE)

### Sample Event History (Event 2157)

```
id=3099, captured=2026-02-02 11:30:11, status=new/changed, markets=153
id=4313, captured=2026-02-02 11:51:54, status=new/changed, markets=153
id=5275, captured=2026-02-02 12:05:32, status=new/changed, markets=153
...
```

**Observation:** This event has 90 snapshots over 4 days, with scrapes approximately every 10-20 minutes during active periods.

---

## 2. Storage Analysis

### Table Sizes

| Table | Data Size | Total Size (w/indexes) | Row Count |
|-------|-----------|------------------------|-----------|
| `competitor_odds_snapshots` | 18 MB | **6.4 GB** | 150,018 |
| `odds_snapshots_default` (partitioned) | 10 MB | **4.4 GB** | 90,341 |
| `market_odds` | 3.2 GB | **3.7 GB** | 15,126,528 |
| `competitor_market_odds` | 3.0 GB | **3.5 GB** | 12,404,645 |
| `events` | 312 KB | 576 KB | 185 |

**Total Database Size: 18 GB**

### Per-Snapshot Metrics

- **Average markets per snapshot:** 167.4
- **Average snapshots per event:** 51.8
- **Average total markets per event:** 8,668

### Storage Per Market Row (Estimated)

Based on table sizes:
- `market_odds`: 3.7 GB / 15.1M rows = **~257 bytes/row** (including indexes)
- Each row stores: market_id, name, line, handicap fields, JSONB outcomes, market_groups

### Storage Projection Formula

```
Storage per event per day =
  (scrapes_per_day × change_rate × markets_per_snapshot × bytes_per_market)

With current settings (10-min interval):
- scrapes_per_day = 144
- estimated change_rate = 50% (based on analysis)
- markets_per_snapshot = 167
- bytes_per_market = 257

= 144 × 0.5 × 167 × 257 = 3.1 MB per event per day
```

### Storage Projections

| Retention Period | Events | Estimated Storage |
|-----------------|--------|-------------------|
| 7 days | 100 | 2.2 GB |
| 30 days | 100 | 9.3 GB |
| 90 days | 100 | 27.9 GB |
| 7 days | 500 | 10.9 GB |
| 30 days | 500 | 46.5 GB |

---

## 3. Change Frequency Analysis

### Scrape Cycle Analysis

**Current configuration:**
- Scrape interval: **10 minutes**
- Scrapes per day: **144**

### Hourly Snapshot Creation (24h sample)

```
2026-02-05 15:00 - 5,145 new snapshots
2026-02-05 16:00 - 4,553 new snapshots
2026-02-06 09:00 - 4,687 new snapshots
2026-02-06 10:00 - 4,543 new snapshots
2026-02-06 11:00 - 5,866 new snapshots
```

**Peak activity:** ~5,000-6,000 snapshots/hour during busy periods.

### Change Rate Per Event

**Sample analysis (event 2158 with 90 snapshots):**
- Unchanged confirmations: 24 (26.7%)
- New/changed: 66 (73.3%)

**Interpretation:**
- **~73% of scrape cycles result in new snapshots** (odds changed)
- **~27% of cycles just confirm existing data** (UPDATE last_confirmed_at)
- Odds change frequently for active events (multiple times per hour)

### Change Detection Behavior

From `src/caching/change_detection.py`:
1. Compare cached markets against scraped markets using normalized outcome tuples
2. If ANY market's odds changed: **INSERT new snapshot** (all markets)
3. If NO changes: **UPDATE last_confirmed_at** on existing snapshot

**Key insight:** Even a single market odds change triggers a full snapshot INSERT.

---

## 4. Current Retention Behavior

### Settings Configuration

```sql
SELECT odds_retention_days, match_retention_days, cleanup_frequency_hours
FROM settings WHERE id = 1;
```

**Results:**
- `odds_retention_days`: **30**
- `match_retention_days`: **30**
- `cleanup_frequency_hours`: **24**

### Cleanup Mechanism

From `src/services/cleanup.py`:

1. **Odds cleanup:** DELETE snapshots where `captured_at < NOW() - retention_days`
2. **Match cleanup:** DELETE events where `kickoff < NOW() - retention_days`
3. **Cascade:** market_odds deleted via foreign key cascade
4. **Orphan cleanup:** Tournaments without events are deleted

### Cleanup History

**No cleanup runs recorded yet** - the system has been running for ~4 days, which is less than the 30-day retention period.

### What is Lost on Cleanup

When cleanup runs:
- **ALL historical snapshots** older than retention period are deleted
- No sampling or aggregation is performed
- Raw response data is lost
- Market-level historical odds are lost

---

## Current Architecture Implications

### Write Pipeline Flow

```
Scrape → Change Detection → Write Queue → DB
                ↓
         Cache updated
         on INSERT
```

1. **INSERT path (odds changed):**
   - New OddsSnapshot row created
   - All MarketOdds rows created (even unchanged markets)
   - Cache updated with new snapshot_id

2. **UPDATE path (odds unchanged):**
   - Existing snapshot's `last_confirmed_at` updated
   - No new rows created
   - Cache not updated (already has this data)

### Schema Structure (Current)

```
odds_snapshots (partitioned by captured_at)
├── id (BIGINT PK)
├── event_id (FK → events)
├── bookmaker_id (FK → bookmakers)
├── captured_at (TIMESTAMP)
├── scrape_run_id (FK → scrape_runs, nullable)
├── raw_response (JSONB, nullable)
└── last_confirmed_at (TIMESTAMP, nullable)

market_odds
├── id (BIGINT PK)
├── snapshot_id (FK → odds_snapshots)
├── betpawa_market_id (VARCHAR)
├── betpawa_market_name (VARCHAR)
├── line (FLOAT, nullable)
├── handicap_type (VARCHAR, nullable)
├── handicap_home (FLOAT, nullable)
├── handicap_away (FLOAT, nullable)
├── outcomes (JSONB)
└── market_groups (JSONB, nullable)
```

---

## Design Recommendations

### Recommended Strategy: Option C - Change-Based Retention with Extended History

**Rationale:**
1. Current system already creates snapshots only on change
2. Storage is dominated by market_odds rows (257 bytes each × 167 markets = 43KB per snapshot)
3. Keeping all change-based snapshots provides accurate historical data without interpolation

### Proposed Changes

#### 1. No Schema Changes Required

The current schema already supports historical tracking:
- `odds_snapshots` stores multiple rows per event
- `captured_at` provides temporal ordering
- `last_confirmed_at` indicates data validity window
- Partitioning by `captured_at` supports efficient cleanup

#### 2. New Configuration Option

Add to `Settings` model:

```python
# Historical retention (separate from operational retention)
historical_retention_days: Mapped[int] = mapped_column(default=90)
```

#### 3. Cleanup Modification

Current cleanup deletes by `captured_at`. Modify to support:
- **Operational data:** Keep last N days (current behavior)
- **Historical summary:** Optional aggregation before deletion

#### 4. Query Index Additions

For efficient historical queries:

```sql
-- Query pattern: "Get odds history for event X, market Y over time range"
CREATE INDEX idx_market_odds_snapshot_market
ON market_odds (snapshot_id, betpawa_market_id);

-- Query pattern: "Get all snapshots for event X in time range"
-- (Already exists: idx_snapshots_event_time)
```

### API Query Patterns Supported

1. **Odds trend for event+market:**
   ```sql
   SELECT s.captured_at, m.outcomes
   FROM odds_snapshots s
   JOIN market_odds m ON m.snapshot_id = s.id
   WHERE s.event_id = ?
     AND m.betpawa_market_id = ?
     AND s.captured_at BETWEEN ? AND ?
   ORDER BY s.captured_at;
   ```

2. **Margin history for event:**
   ```sql
   SELECT s.captured_at, m.outcomes
   FROM odds_snapshots s
   JOIN market_odds m ON m.snapshot_id = s.id
   WHERE s.event_id = ?
     AND m.betpawa_market_id = '1X2'  -- 1X2 market for margin calc
   ORDER BY s.captured_at;
   ```

3. **All snapshots for event in time range:**
   ```sql
   SELECT s.*, COUNT(m.id) as market_count
   FROM odds_snapshots s
   LEFT JOIN market_odds m ON m.snapshot_id = s.id
   WHERE s.event_id = ?
     AND s.captured_at BETWEEN ? AND ?
   GROUP BY s.id
   ORDER BY s.captured_at;
   ```

### Storage Optimization Opportunities

1. **Remove raw_response storage** - Currently nullable, rarely needed for historical analysis
2. **Outcome compression** - JSONB outcomes could use abbreviated keys
3. **Selective market retention** - Only store key markets (1X2, Over/Under) for history

### Phase 61 Implementation Outline

1. **Task 1:** Add `historical_retention_days` setting (Alembic migration)
2. **Task 2:** Create historical query endpoints in API
3. **Task 3:** Update cleanup to respect historical retention
4. **Task 4:** Add index for efficient historical queries
5. **Task 5:** Frontend components for odds history visualization

---

## Summary

| Aspect | Finding |
|--------|---------|
| **Current behavior** | Multiple snapshots kept per event (avg 52) |
| **Storage growth** | ~3.1 MB/event/day at current settings |
| **Change rate** | ~73% of scrapes result in new snapshots |
| **Retention** | 30 days configured, no cleanup run yet |
| **Schema changes needed** | Minimal - add retention setting |
| **Index changes** | One composite index recommended |
| **Risk** | Storage growth at scale (500 events × 90 days = 139 GB) |
