# API/UI Data Flow Audit Report

**Phase 34.1: API/UI Data Flow Audit**
**Date:** 2026-01-28

---

## Executive Summary

The audit identified **3 significant issues** in the data flow pipeline:

1. **API Bug (Critical):** `/palimpsest/coverage` counts raw competitor rows instead of unique events, inflating competitor_only_count by ~92% (254 vs 132 actual)
2. **Architecture Gap (Major):** Event detail endpoint uses legacy odds system with limited competitor data (506 events) vs new system (2,400+ events)
3. **Stale Odds Display (Major):** Event detail shows competitor odds from 2026-01-24 (4 days old) despite fresh data existing in competitor_odds_snapshots

The backend matching system remains healthy (99.9% accurate per Phase 34). The issues are in how data is **queried and presented**, not stored.

---

## 1. API Layer Findings

### API-001: Competitor-Only Count Not Deduplicated (Critical)

**Location:** `src/api/routes/palimpsest.py:119-127`

**Description:**
The `/palimpsest/coverage` endpoint counts competitor-only events using raw row count instead of distinct SportRadar IDs. Since the same event can exist on both SportyBet and Bet9ja, this double-counts events.

**Evidence:**
```sql
-- What API does (raw count):
SELECT COUNT(*) FROM competitor_events
WHERE betpawa_event_id IS NULL AND kickoff > NOW();
-- Result: 254

-- What it SHOULD do (distinct SR IDs):
SELECT COUNT(DISTINCT sportradar_id) FROM competitor_events
WHERE betpawa_event_id IS NULL AND kickoff > NOW();
-- Result: 132
```

**API Response showing discrepancy:**
```json
// GET /palimpsest/coverage
{
  "total_events": 1295,        // WRONG: inflated
  "competitor_only_count": 254, // WRONG: should be 132
  "match_rate": 75.83          // WRONG: skewed by inflated total
}

// GET /palimpsest/events shows correct data after deduplication:
{
  "total_events": 1173,        // CORRECT
  "competitor_only_count": 132 // Implicit (matches + bp_only + comp_only)
}
```

**Impact:**
- Coverage stats cards show inflated "competitor-only" count
- Match rate percentage is artificially low (75.8% vs actual ~83.7%)
- Inconsistent data between `/coverage` and `/events` endpoints

**Fix Approach (Phase 35):**
Change line 119-127 from:
```python
competitor_only_query = (
    select(func.count())
    .select_from(CompetitorEvent)
    .where(CompetitorEvent.betpawa_event_id.is_(None))
)
```
To:
```python
competitor_only_query = (
    select(func.count(distinct(CompetitorEvent.sportradar_id)))
    .where(CompetitorEvent.betpawa_event_id.is_(None))
)
```

---

### API-002: Event Detail Uses Legacy Odds Architecture (Major)

**Location:** `src/api/routes/events.py:640-667`

**Description:**
The `/events/{id}` endpoint fetches competitor odds from the legacy `event_bookmakers` + `odds_snapshots` tables. However, the new v1.1 architecture stores competitor odds in `competitor_events` + `competitor_odds_snapshots`. This means event detail views show incomplete or stale competitor data.

**Evidence:**
```sql
-- Legacy system (used by API):
SELECT b.slug, COUNT(DISTINCT os.event_id)
FROM odds_snapshots os
JOIN bookmakers b ON os.bookmaker_id = b.id
JOIN events e ON os.event_id = e.id
WHERE e.kickoff > NOW()
GROUP BY b.slug;
-- sportybet: 506 events, bet9ja: 413 events, betpawa: 1041 events

-- New system (NOT used by event detail):
SELECT source, COUNT(DISTINCT competitor_event_id)
FROM competitor_odds_snapshots cos
JOIN competitor_events ce ON cos.competitor_event_id = ce.id
WHERE ce.kickoff > NOW()
GROUP BY source;
-- sportybet: 1113 events, bet9ja: 1309 events
```

**Impact:**
- Event detail page shows "no odds" for many competitors
- ~50% of competitor odds data is invisible in detail view
- Users see incomplete competitive comparison

**Fix Approach (Phase 35):**
Modify `get_event()` to also query `competitor_events` + `competitor_odds_snapshots` when displaying matched events. This requires:
1. Look up competitor events by `betpawa_event_id` match
2. Load their latest `competitor_odds_snapshots`
3. Merge into the response alongside legacy data

---

### API-003: Dual Storage Architecture Creates Confusion (Minor)

**Location:** Architecture-level (not single file)

**Description:**
The codebase maintains two parallel systems for competitor odds:
1. **Legacy (v1.0):** `event_bookmakers` + `odds_snapshots` - filtered by BetPawa events
2. **New (v1.1):** `competitor_events` + `competitor_odds_snapshots` - full palimpsest

Both are being written to, but different endpoints read from different systems.

**Evidence:**
| Endpoint | Data Source | Completeness |
|----------|-------------|--------------|
| `/events` (list) | Legacy odds_snapshots | Partial competitor coverage |
| `/events/{id}` | Legacy odds_snapshots | Partial competitor coverage |
| `/palimpsest/coverage` | New competitor_events | Full coverage |
| `/palimpsest/events` | New competitor_events | Full coverage |

**Impact:**
- Confusing data inconsistencies
- Maintenance burden of two systems
- Some features show different data than others

**Fix Approach (Phase 35+):**
Either:
1. **Short-term:** Have event endpoints also query new tables
2. **Long-term:** Deprecate legacy tables, use new architecture everywhere

---

## 2. Frontend Layer Findings

### FE-001: React Query Configuration is Correct (No Issue)

**Location:**
- `web/src/features/matches/hooks/use-matches.ts:31-33`
- `web/src/features/coverage/hooks/use-coverage.ts:9-11`

**Analysis:**
React Query configuration is appropriate for this use case:
- `staleTime: 30000` (30s) - reasonable for odds data
- `gcTime: 60000` (60s) - appropriate garbage collection
- `refetchInterval: 60000` (60s polling) - standard refresh rate

No caching issues identified. Data staleness is caused by API layer (API-002), not frontend caching.

---

### FE-002: Coverage Stats Display Passes Through API Bug (Indirect)

**Location:** `web/src/features/coverage/components/stats-cards.tsx:47-127`

**Description:**
The Coverage page correctly displays data from the API, but since the API returns incorrect `competitor_only_count` (API-001), the UI shows wrong numbers.

**Evidence:**
UI displays:
- Total Events: 1295 (inflated)
- Match Rate: 75.83% (incorrect)

Should display:
- Total Events: 1173
- Match Rate: 83.72%

**Impact:** Users see misleading coverage statistics.

**Fix Approach:** Fixing API-001 will automatically fix this UI issue.

---

### FE-003: Odds Comparison Table Works Correctly (No Issue)

**Location:** `web/src/features/matches/components/match-table.tsx`

**Analysis:**
The match table correctly:
- Displays odds from `inline_odds` array
- Color-codes based on competitive position
- Handles missing odds gracefully (shows "-")

The stale competitor odds issue (visible when clicking into detail) is caused by API-002, not frontend logic.

---

### FE-004: No Client-Side Filtering Issues Identified

**Analysis:**
Reviewed all frontend code for:
- Client-side filtering that could hide valid data
- State management issues
- Data transformation bugs

No issues found. Frontend faithfully renders what API provides.

---

## 3. Root Cause Analysis

### Mapping UAT Symptoms to Root Causes

| Symptom | Root Cause | Bug ID |
|---------|-----------|--------|
| "Too many matches showing as unmatched" | API double-counts competitor-only events | API-001 |
| "Odds not correctly updated / stale values" | Event detail uses legacy odds system | API-002 |
| "Overall poor data quality in UI" | Combination of API-001 + API-002 | - |
| "Wrong coverage matching and mapping" | Inflated competitor_only_count | API-001 |

### Why Backend Is Healthy But UI Shows Bad Data

The Phase 34 audit confirmed the **matching system** is 99.9% accurate. The issues are:

1. **Query bugs** - API queries the wrong tables or doesn't deduplicate
2. **Architecture gap** - New data exists but isn't being served to UI
3. **Not data corruption** - The underlying data is correct

---

## 4. Recommended Fix Order (Phase 35+)

### Priority 1: Fix API-001 (Est. 15 min)
**Why first:** Single line change with immediate visible improvement on Coverage page.

### Priority 2: Fix API-002 (Est. 2-4 hours)
**Why second:** Requires more work but enables full competitive comparison in event detail.

### Priority 3: Address API-003 Architecture (Est. deferred)
**Why deferred:** Low urgency; can be addressed as part of larger refactoring if needed.

---

## 5. SQL Verification Queries

These queries can be used to verify fixes are working:

```sql
-- Verify API-001 fix (should match frontend coverage stats)
SELECT
    COUNT(DISTINCT CASE WHEN ce.betpawa_event_id IS NOT NULL THEN ce.betpawa_event_id END) as matched,
    (SELECT COUNT(*) FROM events WHERE kickoff > NOW()) -
        COUNT(DISTINCT CASE WHEN ce.betpawa_event_id IS NOT NULL THEN ce.betpawa_event_id END) as betpawa_only,
    COUNT(DISTINCT CASE WHEN ce.betpawa_event_id IS NULL THEN ce.sportradar_id END) as competitor_only
FROM competitor_events ce
WHERE ce.kickoff > NOW() AND ce.deleted_at IS NULL;

-- Verify API-002 (check odds freshness per bookmaker)
SELECT
    b.slug,
    MAX(os.captured_at) as latest_snapshot,
    COUNT(DISTINCT os.event_id) as events_with_odds
FROM odds_snapshots os
JOIN bookmakers b ON os.bookmaker_id = b.id
JOIN events e ON os.event_id = e.id
WHERE e.kickoff > NOW()
GROUP BY b.slug;
```

---

## 6. Conclusion

The UAT issues from Phase 34 (UAT-001) are now fully explained:

1. **Root cause identified:** API query bugs and architecture gaps, not data corruption
2. **Backend is healthy:** Matching accuracy remains 99.9%
3. **Fixes are straightforward:** API-001 is a one-line fix; API-002 requires modest refactoring
4. **No frontend bugs found:** UI correctly displays what API provides

**Recommendation:** Proceed to Phase 35 for remediation, prioritizing API-001 as a quick win.

---

*Report generated: 2026-01-28*
*Phase: 34.1-api-ui-data-flow-audit*
*Audit duration: ~30 minutes*
