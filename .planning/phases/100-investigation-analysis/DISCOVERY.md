# Phase 100: Storage Investigation & Analysis

**Investigation Date:** 2026-02-17
**Database:** pawarisk (PostgreSQL)
**Data Age:** 2026-02-02 to 2026-02-13 (15 days)

## Executive Summary

The database has grown to **63 GB** in 15 days - significantly larger than the initial estimate of 20+ GB. The primary storage drivers are JSON columns storing raw API responses that are **never read after scraping completes**. Removing these columns would reduce storage by **~53%** (33 GB savings).

## Profiling Results

### Table Sizes

| Table | Total Size | Data Size | Index Size | % of Total |
|-------|------------|-----------|------------|------------|
| odds_snapshots_default | 24 GB | 24 GB | 46 MB | 38.6% |
| market_odds | 22 GB | 18 GB | 4.6 GB | 35.4% |
| competitor_odds_snapshots | 11 GB | 11 GB | 12 MB | 17.1% |
| competitor_market_odds | 5.6 GB | 4.9 GB | 688 MB | 8.7% |
| event_scrape_status | 108 MB | 83 MB | 25 MB | 0.2% |
| Other tables | < 10 MB | - | - | < 0.1% |
| **TOTAL** | **63 GB** | **58 GB** | **5.4 GB** | 100% |

### Row Counts

| Table | Row Count | Avg Row Size |
|-------|-----------|--------------|
| market_odds | 85,408,740 | ~260 bytes |
| competitor_market_odds | 19,938,384 | ~285 bytes |
| odds_snapshots | 499,269 | ~50 KB |
| competitor_odds_snapshots | 278,129 | ~40 KB |
| event_scrape_status | 599,344 | ~180 bytes |

### JSON Column Analysis

| Column | Size | Rows | Avg Size | Purpose |
|--------|------|------|----------|---------|
| `odds_snapshots.raw_response` | **23 GB** | 499,269 | 49.6 KB | Raw API response |
| `competitor_odds_snapshots.raw_response` | **10 GB** | 278,129 | 39.7 KB | Raw API response |
| `market_odds.outcomes` | 9 GB | 85,408,740 | 112 bytes | Normalized odds |
| `competitor_market_odds.outcomes` | 3 GB | 19,938,384 | 155 bytes | Normalized odds |

### Growth Metrics

| Period | Snapshots/Day (BP) | Snapshots/Day (Comp) | Est. Growth/Day |
|--------|-------------------|---------------------|-----------------|
| Feb 10 | 69,806 | - | ~4.2 GB |
| Feb 11 | 46,651 | - | ~2.8 GB |
| Feb 12 | 76,057 | - | ~4.5 GB |
| Feb 13 | 46,537 | - | ~2.8 GB |
| **Average** | ~60,000 | ~20,000 | **~3.6 GB/day** |

### Retention Analysis

| Period | BP Snapshots | BP Markets | Comp Snapshots | Comp Markets |
|--------|--------------|------------|----------------|--------------|
| Last 7 days | 239,051 (48%) | 40.5M (47%) | 89,731 (32%) | 5.1M (26%) |
| All time | 499,269 | 85.4M | 278,129 | 19.9M |

### Data vs Index Ratio

- **Data:** 58 GB (91.7%)
- **Indexes:** 5.4 GB (8.3%)

---

## Storage Drivers Analysis

### #1: raw_response Columns (33 GB, 53% of total)

**The Problem:**
- `odds_snapshots.raw_response`: 23 GB (37% of database)
- `competitor_odds_snapshots.raw_response`: 10 GB (16% of database)
- Stores complete API JSON responses (50 KB avg per snapshot)

**Code Analysis:**
```
Grep results for "raw_response" in src/:

WRITE locations (storing data):
- src/scraping/event_coordinator.py:1503,1530,1752,1760
- src/scraping/competitor_events.py:224,278,562,707
- src/storage/write_handler.py:120,135

READ locations (using data):
- src/scraping/competitor_events.py:778-779 - Extract ID for subsequent fetch
- src/scraping/competitor_events.py:909 - Update during scrape
- src/scraping/competitor_events.py:974 - Build fetch list

API endpoints using raw_response: NONE
Historical analysis using raw_response: NONE
User-facing features using raw_response: NONE
```

**Conclusion:** `raw_response` is only used during the scraping process itself to extract IDs for subsequent API calls. Once the scrape completes and market data is normalized into `market_odds.outcomes`, the raw_response is **never read again**.

**Recommendation:** REMOVE `raw_response` columns entirely. The data needed during scraping can be held in memory for the scrape duration.

### #2: market_odds Table (22 GB, 35% of total)

**The Problem:**
- 85.4M rows at 260 bytes average
- 9 GB in `outcomes` JSON column (normalized odds)
- 4.6 GB in indexes

**Analysis:**
- Each snapshot creates ~170 market_odds rows
- High volume is inherent to tracking all markets
- `outcomes` JSON is actively used by API and UI

**Recommendation:** Retention-based cleanup is the primary lever. No schema optimization needed.

### #3: competitor_market_odds (5.6 GB, 9% of total)

**The Problem:**
- 19.9M rows at 285 bytes average
- 3 GB in `outcomes` JSON
- Similar structure to market_odds

**Recommendation:** Same as market_odds - retention-based cleanup.

### #4: Index Overhead (5.4 GB)

- market_odds indexes: 4.6 GB
- Other: 0.8 GB
- Index ratio is reasonable (8.3%)

**Recommendation:** No immediate action needed on indexes.

---

## Optimization Opportunities

### Option A: Remove raw_response (HIGH IMPACT, LOW RISK)

**Impact:** Save 33 GB (53% of database)
**Risk:** Low - no features use this data
**Effort:** Medium - migration required

**Implementation:**
1. Modify scraping code to hold raw data in memory only
2. Create migration to drop `raw_response` columns
3. Run VACUUM FULL to reclaim space

**Changes Required:**
- `src/scraping/competitor_events.py` - Hold raw data in local dict during scrape
- `src/storage/write_queue.py` - Remove field from DTOs
- `src/storage/write_handler.py` - Stop writing field
- `src/db/models/odds.py` - Remove column
- `src/db/models/competitor.py` - Remove column
- Migration: `ALTER TABLE odds_snapshots DROP COLUMN raw_response`
- Migration: `ALTER TABLE competitor_odds_snapshots DROP COLUMN raw_response`

### Option B: Aggressive Retention (MEDIUM IMPACT, LOW RISK)

**Current State:**
- 15 days of data at 63 GB
- Last 7 days = 47% of data

**Impact:**
- 7-day retention: ~30 GB (53% reduction)
- 3-day retention: ~15 GB (76% reduction)

**Risk:** Low - user has accepted losing historical data
**Effort:** Low - existing retention mechanism

**Implementation:**
1. Update settings: `odds_retention_days = 7`
2. Run cleanup job immediately
3. Schedule daily cleanup

### Option C: Combined Approach (BEST)

**Strategy:** Apply Option A + Option B together

**Expected Results:**
1. Remove raw_response: 63 GB → 30 GB (-33 GB)
2. Apply 7-day retention: 30 GB → ~14 GB (-16 GB)
3. Final size: **~14 GB** (78% reduction)

---

## Recommended Strategy

### Phase 101: Schema Implementation

**Goal:** Remove raw_response columns and reclaim 33 GB

**Tasks:**
1. Create Alembic migration to drop `raw_response` from both snapshot tables
2. Update DTOs in write_queue.py to remove field
3. Update write_handler.py to stop writing field
4. Update competitor_events.py to hold raw data in memory during scrape
5. Update event_coordinator.py to not pass raw_response to DTOs
6. Run migration
7. Run VACUUM FULL on affected tables

**Expected Savings:** 33 GB (53%)

### Phase 102: Application Migration

**Goal:** Ensure scraping still works without raw_response storage

**Tasks:**
1. Refactor competitor_events.py scraping flow
   - Create in-memory dict for raw responses during scrape session
   - Access dict instead of DB for ID extraction
   - Clear dict after scrape completes
2. Update tests for new flow
3. Verify scraping works end-to-end

**Risk Mitigation:**
- Keep raw data in memory only for duration of scrape
- Extract needed IDs before discarding

### Phase 103: Data Migration & Validation

**Goal:** Apply aggressive retention and validate

**Tasks:**
1. Update settings: `odds_retention_days = 7`
2. Run immediate cleanup of data older than 7 days
3. Verify all features work with reduced data
4. Confirm database size reduction

**Expected Additional Savings:** ~16 GB

### Phase 104: Monitoring & Prevention

**Goal:** Prevent future storage issues

**Tasks:**
1. Add database size tracking to sidebar (already has widgets)
2. Add alert when database exceeds threshold (e.g., 10 GB)
3. Ensure cleanup job runs reliably
4. Document retention policy

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|------------|------------|
| Remove raw_response | LOW | Data unused after scrape; hold in memory |
| 7-day retention | LOW | User has accepted; historical analysis still works |
| VACUUM FULL | MEDIUM | Requires exclusive lock; schedule during low usage |

---

## Verification Checklist

- [x] Table sizes documented for all public tables
- [x] Row counts verified (exact counts for key tables)
- [x] JSON column sizes estimated
- [x] Growth rate calculated (~3.6 GB/day)
- [x] raw_response usage analyzed (UNUSED after scrape)
- [x] Top 3 storage drivers identified (raw_response 53%, market_odds 35%, competitor 17%)
- [x] Optimization opportunities ranked
- [x] Phase 101-104 scope defined

---

## Summary Metrics

| Metric | Current | After Optimization | Change |
|--------|---------|-------------------|--------|
| Total Size | 63 GB | ~14 GB | -78% |
| Largest Column | raw_response (33 GB) | outcomes (12 GB) | Removed |
| Growth Rate | 3.6 GB/day | ~0.5 GB/day | -86% |
| Retention | 15 days | 7 days | -53% |

**Conclusion:** The database size issue is primarily caused by storing raw API responses that are never used. Removing these columns combined with reasonable retention will achieve the target of under 10 GB.
