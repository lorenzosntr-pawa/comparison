# Phase 87: Availability Tracking Discovery

## Data Analysis (Task 1)

### 1. Current Data Volume

| Table | Row Count |
|-------|-----------|
| events | 3,045 |
| odds_snapshots | 350,838 |
| market_odds | 60,544,524 |
| competitor_events | 7,669 |
| competitor_odds_snapshots | 211,863 |
| competitor_market_odds | 16,291,440 |

### 2. Event-Level Coverage Analysis

**Betpawa Events (last 7 days): 2,790**
- 100% have at least one snapshot (as expected - single bookmaker platform)

**Competitor Events (last 7 days): 3,698**
- 377 events (10.19%) have data from only 1 competitor
- 3,321 events (89.81%) have data from both competitors (SportyBet + Bet9ja)

**Cross-Platform Coverage Gaps:**
| Coverage Type | Event Count |
|---------------|-------------|
| betpawa_only | 5 |
| both | 2,785 |
| competitor_only | 913 |

**Finding:** 913 events exist only in competitor data (no Betpawa match). These represent events Betpawa doesn't offer but competitors do.

### 3. Snapshot Timeline Continuity

```sql
-- Events with 2+ hour spans
SELECT bookmaker, AVG(coverage_ratio) as avg_coverage
-- Result: betpawa = 56.8% coverage ratio
```

**Finding:** Events average 34 hours of snapshot data over an 80-hour expected span - only **56.8% coverage ratio**. Significant gaps exist in snapshot timelines due to:
- Scraping intervals
- API failures
- Events removed early by bookmaker

### 4. Market-Level Disappearance Patterns

**Markets with Lowest Presence Over Event Lifetime:**

| Market | Events | Avg Hours Present | Avg Event Hours | Presence % |
|--------|--------|-------------------|-----------------|------------|
| Total Bookings {home/away} First Half | 25 | 9 | 53 | 15.25% |
| Total Bookings First Half | 40 | 11 | 57 | 19.67% |
| Total Corners First Half | 84 | 16 | 55 | 26.10% |
| Total Bookings Full Time | 45 | 19 | 60 | 29.78% |

**Markets That Disappear Early (>2 hours before latest snapshot):**

| Market | Total | Disappeared Early | Early Disappear % |
|--------|-------|-------------------|-------------------|
| Win Both Halves {away} | 452 | 50 | 11.06% |
| Last Goalscorer | 56 | 3 | 5.36% |
| Last Corner First Half | 46 | 2 | 4.35% |

**Finding:** Markets DO disappear over time. Many specialized markets (bookings, corners, in-play markets) have low presence rates (15-30%). Some markets disappear before event kickoff.

### 5. Outcome Suspension Analysis

```sql
-- Suspension rate (last 7 days)
SELECT
    COUNT(*) as total_outcomes,
    SUM(CASE WHEN is_active = false THEN 1 ELSE 0 END) as suspended,
    suspension_pct
-- Result: 127,418,024 total, 60,454 suspended (0.0474%)
```

**Finding:** Outcome suspension (`is_active=false`) is very rare - only **0.0474%** of outcomes are suspended. This is already handled with strikethrough styling in the UI.

**Sample Suspended Outcomes:**
- "1X2 and Over/Under | Full Time" - various combo outcomes suspended
- "Double Chance and Over/Under | Full Time" - suspended during live play

### 6. Competitor-Specific Market Coverage

**Bet9ja Lowest Coverage Markets (of 3,408 events):**

| Market | Events | Coverage % |
|--------|--------|------------|
| Team with Most Bookings 3-Way - First Half | 79 | 2.32% |
| Total Bookings Over/Under - First Half | 102 | 2.99% |
| Sending Off markets | 107 | 3.14% |
| Last Corner markets | 514 | 15.08% |
| Asian Handicap - Full Time | 1714 | 50.29% |

**Finding:** Bet9ja has very low coverage for specialized markets (bookings, corners, sendings-off). Core markets (1X2, Over/Under) have near 100% coverage.

### 7. Cache Implications

Current cache behavior:
- `OddsCache` stores only the latest snapshot per event/bookmaker
- When a market disappears from scrape, it's simply absent from cache
- API returns `null` for missing markets (displayed as "-" in UI)
- **No distinction between "never offered" and "was available, now unavailable"**

**Key Challenge:** Detecting absences requires comparing new scrape to previous cache state.

---

## Design Specification (Task 2)

### Design Decision: Option B - `unavailable_at` Timestamp + Cache-Level Detection

After evaluating all options, **Option B** is recommended for these reasons:

1. **Minimal schema change** - Single nullable timestamp column
2. **Query-friendly** - Can ask "when did this become unavailable?"
3. **Storage efficient** - No separate table, no history overhead
4. **Implementation clean** - Detection logic in cache layer, minimal code changes

### Schema Changes

#### 1. MarketOdds / CompetitorMarketOdds

Add `unavailable_at` column:

```sql
ALTER TABLE market_odds
ADD COLUMN unavailable_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE competitor_market_odds
ADD COLUMN unavailable_at TIMESTAMP WITH TIME ZONE;
```

**Semantics:**
- `NULL` = market is available (default, most common)
- Timestamp = market became unavailable at this time

**Why not `available` boolean?**
- Boolean doesn't tell us WHEN it became unavailable
- Timestamp enables "Unavailable since X" tooltips
- Can derive boolean from `unavailable_at IS NULL`

### Cache Changes

#### 2. CachedMarket Dataclass

Add `unavailable_at` field:

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
    unavailable_at: datetime | None  # NEW: None = available

@property
def is_available(self) -> bool:
    return self.unavailable_at is None
```

### Detection Logic

#### 3. Availability Detection in Scraping Pipeline

**Location:** `src/caching/change_detection.py` or new `src/caching/availability_detection.py`

```python
def detect_availability_changes(
    previous_markets: dict[str, CachedMarket],  # market_key -> CachedMarket
    new_market_data: list[ScrapedMarket],
    timestamp: datetime
) -> tuple[list[CachedMarket], list[str]]:
    """
    Compare previous cache state to new scrape results.

    Returns:
        - updated_markets: Markets with availability changes
        - disappeared_keys: Market keys that disappeared (for logging)
    """
    new_market_keys = {get_market_key(m) for m in new_market_data}
    previous_keys = set(previous_markets.keys())

    # Markets that were available but are now missing
    disappeared = previous_keys - new_market_keys

    # Markets that returned (were unavailable, now available)
    returned = new_market_keys - previous_keys

    updated = []
    for key in disappeared:
        prev = previous_markets[key]
        if prev.unavailable_at is None:  # Was available, now gone
            updated.append(replace(prev, unavailable_at=timestamp))

    for key in returned:
        if key in previous_markets:
            prev = previous_markets[key]
            if prev.unavailable_at is not None:  # Was unavailable, now back
                updated.append(replace(prev, unavailable_at=None))

    return updated, list(disappeared)
```

**Integration Point:** After `store_batch_results()` in `EventCoordinator`, call availability detection:

```python
# In event_coordinator.py after scraping completes for an event
previous_cache = self.odds_cache.get_betpawa_snapshot(event_id)
if previous_cache:
    previous_markets = {get_market_key(m): m for m in previous_cache.markets}
    updated, disappeared = detect_availability_changes(
        previous_markets,
        new_scraped_markets,
        datetime.utcnow()
    )
    # Update cache with availability changes
    for market in updated:
        self.odds_cache.update_market_availability(event_id, market)
```

### API Changes

#### 4. API Response Schema

Add availability fields to market response:

```python
class InlineMarketOdds(BaseModel):
    market_id: str
    market_name: str
    outcomes: list[OutcomeOdds]
    line: float | None = None
    # NEW: Availability fields
    available: bool = True
    unavailable_since: datetime | None = None  # For tooltip
```

**API Response Example:**

```json
{
  "market_id": "3743",
  "market_name": "1X2 | Full Time",
  "outcomes": [{"name": "1", "odds": 2.10}],
  "available": true,
  "unavailable_since": null
}

// Market that became unavailable:
{
  "market_id": "5000",
  "market_name": "Over/Under | Full Time",
  "outcomes": [],
  "available": false,
  "unavailable_since": "2026-02-11T14:30:00Z"
}
```

### UI Changes (Preview for Phases 90-91)

#### 5. Odds Comparison Display

```tsx
// OddsBadge enhancement
if (!market.available) {
  return (
    <Tooltip content={`Unavailable since ${formatRelative(market.unavailable_since)}`}>
      <span className="text-muted-foreground line-through">—</span>
    </Tooltip>
  )
}

// vs "never offered" (null market):
if (market === null) {
  return <span className="text-muted-foreground">-</span>
}
```

**Visual distinction:**
- `null` (never offered): Plain dash "-"
- `available=false` (became unavailable): Strikethrough dash "~~—~~" with tooltip

### History Charts (Preview for Phase 92)

#### 6. Timeline Visualization

Availability transitions can be shown in history charts:

```tsx
// Dotted/dashed line for unavailable periods
<Line
  dataKey="odds"
  strokeDasharray={point.available ? "0" : "5,5"}
  opacity={point.available ? 1 : 0.5}
/>
```

### Implementation Phases

| Phase | Scope | Work Items |
|-------|-------|------------|
| 88 | Backend | Schema migration, detection logic in scraping pipeline |
| 89 | API/Cache | CachedMarket changes, API response schema, endpoint updates |
| 90 | Odds Comparison UI | Strikethrough styling, tooltips |
| 91 | Event Details UI | Same styling applied to detail page |
| 92 | History Charts | Dotted lines for unavailable periods |

### Edge Cases Addressed

1. **First scrape for event** - No previous state, all markets are "new", no availability tracking needed
2. **Scrape failure vs event unavailability** - Scrape failures don't trigger availability change (retry mechanism)
3. **Temporary suspension** - Market returns? Set `unavailable_at = NULL`
4. **Market never offered** - No record in cache = `null` in API = different from unavailable

### Storage Impact

- **Existing data:** No backfill needed - `unavailable_at` defaults to NULL (available)
- **Going forward:** Minimal overhead - most markets stay available, column rarely populated
- **Index consideration:** Partial index on `unavailable_at IS NOT NULL` for queries

### Trade-offs Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| A: Boolean `available` | Simple | No "when" info | Rejected |
| B: Timestamp `unavailable_at` | Query-friendly, storage efficient | Slightly more complex | **Selected** |
| C: Separate transitions table | Full history | Storage heavy, complex queries | Rejected |
| D: Cache-only detection (no DB) | No migration | Lost on restart | Rejected |

### Success Metrics

After implementation:
- [ ] Can distinguish "never offered" from "became unavailable" in UI
- [ ] Tooltip shows "Unavailable since X" for unavailable markets
- [ ] History charts show availability transitions
- [ ] No performance regression in scraping pipeline
- [ ] No storage issues (< 1% of markets will be marked unavailable)

---

*Phase 87 Investigation completed: 2026-02-11*
*Next: Phase 88 - Backend Availability Tracking*
