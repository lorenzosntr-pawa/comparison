# Bug Report: Specifier Data Mixing in Historical Data Queries

**Severity:** High
**Affected Components:** Backend API, Frontend Dialog, React Hooks
**Bug Type:** Missing Filter Parameter
**Date Identified:** 2026-02-10

## Executive Summary

Historical odds/margin charts for Over/Under and Handicap markets display mixed, nonsensical data because the API filters by `market_id` only, ignoring the `line` specifier. This causes data from different betting lines (e.g., Over 2.5, Over 3.5, Over 4.5) to be combined into a single chart, making the visualization useless and calculations incorrect.

---

## SQL Evidence

### Evidence 1: Markets Store Multiple Different Line Values

The database correctly stores Over/Under markets with different line values under the same `market_id`:

```sql
SELECT DISTINCT betpawa_market_id, betpawa_market_name, line
FROM market_odds
WHERE line IS NOT NULL
ORDER BY betpawa_market_id, line
LIMIT 20;
```

**Result:**
```
 betpawa_market_id |          betpawa_market_name           | line
-------------------+----------------------------------------+------
 1096755           | 1X2 and Over/Under | Full Time         |  1.5
 1096755           | 1X2 and Over/Under | Full Time         |  2.5
 1096755           | 1X2 and Over/Under | Full Time         |  3.5
 1096755           | 1X2 and Over/Under | Full Time         |  4.5
 1096755           | 1X2 and Over/Under | Full Time         |  5.5
 1096755           | 1X2 and Over/Under | Full Time         |  6.5
 1096783           | Total Corners Over/Under | Full Time   |  6.5
 1096783           | Total Corners Over/Under | Full Time   |  7.5
 1096783           | Total Corners Over/Under | Full Time   |  8.5
 1096785           | Corner Asian Handicap | Full Time      | -6.5
 1096785           | Corner Asian Handicap | Full Time      | -0.5
 1096785           | Corner Asian Handicap | Full Time      |  0.5
```

**Analysis:** The same `market_id` (e.g., `1096755`) is used for lines 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5. This is correct data storage, but the API query does not filter by `line`.

### Evidence 2: Events Have Multiple Line Values Per Market

For a single event and market, multiple different lines exist:

```sql
SELECT s.event_id, COUNT(DISTINCT m.line) as different_lines
FROM odds_snapshots s
JOIN market_odds m ON m.snapshot_id = s.id
WHERE m.betpawa_market_id = '1096783'
GROUP BY s.event_id
HAVING COUNT(DISTINCT m.line) > 1
LIMIT 5;
```

**Result:**
```
 event_id | different_lines
----------+-----------------
     2610 |               5
     2607 |               5
     2605 |               5
```

### Evidence 3: Current API Returns Mixed Data

The current API query for event 2610, market `1096783` (Total Corners Over/Under) would return:

```sql
SELECT COUNT(*) as total_rows_returned, COUNT(DISTINCT m.line) as different_lines
FROM odds_snapshots s
JOIN market_odds m ON m.snapshot_id = s.id
WHERE s.event_id = 2610
AND m.betpawa_market_id = '1096783';
```

**Result:**
```
 total_rows_returned | different_lines
---------------------+-----------------
                 770 |               5
```

**Breakdown by line:**
```
 line | rows_per_line
------+---------------
  7.5 |           154
  8.5 |           154
  9.5 |           154
 10.5 |           154
 11.5 |           154
```

**Impact:** When a user clicks "Over 9.5 Corners" to view history, the chart receives 770 data points mixing 5 different lines (7.5, 8.5, 9.5, 10.5, 11.5). The chart is unreadable and calculations are meaningless.

### Evidence 4: Handicap Markets Also Affected

```sql
SELECT m.line, COUNT(*) as rows_per_line
FROM odds_snapshots s
JOIN market_odds m ON m.snapshot_id = s.id
WHERE s.event_id = 2322
AND m.betpawa_market_id = '1096785'
GROUP BY m.line
ORDER BY m.line;
```

**Result:**
```
 line | rows_per_line
------+---------------
  0.5 |            32
  1.5 |            44
  2.5 |            44
  3.5 |            12
```

Asian Handicap markets mix handicap values -0.5, +0.5, +1.5, +2.5, +3.5 together.

---

## Root Cause Analysis

### Backend: Missing Line Filter in SQL Queries

**File:** `src/api/routes/history.py`

**Problem at line 273 (BetPawa odds history query):**
```python
.where(MarketOdds.betpawa_market_id == market_id)
# MISSING: .where(MarketOdds.line == line)  # When line is provided
```

**Problem at line 253 (competitor odds history query):**
```python
.where(CompetitorMarketOdds.betpawa_market_id == market_id)
# MISSING: .where(CompetitorMarketOdds.line == line)  # When line is provided
```

The same pattern repeats in the margin-history endpoint (lines 401-402, 421-422).

### Frontend: Line Not Passed to Dialog

**File:** `web/src/features/matches/components/history-dialog.tsx`

**Problem at lines 60-70 - `HistoryDialogProps` interface:**
```typescript
export interface HistoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  eventId: number
  marketId: string           // <-- PRESENT
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
  allBookmakers?: BookmakerInfo[]
  // MISSING: line?: number | null
}
```

### Frontend: Hook Doesn't Accept Line Parameter

**File:** `web/src/features/matches/hooks/use-odds-history.ts`

**Problem at lines 38-51 - `UseOddsHistoryParams` interface:**
```typescript
export interface UseOddsHistoryParams {
  eventId: number
  marketId: string
  bookmakerSlug: string
  fromTime?: string
  toTime?: string
  enabled?: boolean
  // MISSING: line?: number | null
}
```

### Frontend: API Client Doesn't Pass Line

**File:** `web/src/lib/api.ts`

**Problem at lines 447-461 - `getOddsHistory` function:**
```typescript
getOddsHistory: (params: {
  eventId: number
  marketId: string
  bookmakerSlug: string
  fromTime?: string
  toTime?: string
  // MISSING: line?: number | null
}) => { ... }
```

### Frontend: Callers Don't Pass Line

**File:** `web/src/features/matches/components/market-grid.tsx`

**Problem at lines 40-47 - `HistoryDialogState` interface:**
```typescript
interface HistoryDialogState {
  eventId: number
  marketId: string
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
  allBookmakers: BookmakerInfo[]
  // MISSING: line: number | null
}
```

**Problem at lines 360-368 - `handleHistoryClick` function:**
```typescript
const handleHistoryClick = (bookmakerSlug: string, marketId: string, marketName: string) => {
  setHistoryDialog({
    eventId,
    marketId,           // <-- Passed
    bookmakerSlug,
    marketName,
    bookmakerName: BOOKMAKER_NAMES[bookmakerSlug] ?? bookmakerSlug,
    allBookmakers,
    // MISSING: line,  // Should be passed
  })
}
```

---

## Data Flow Trace

```
User clicks "Over 2.5" odds badge (line=2.5)
  |
  v
handleHistoryClick(bookmakerSlug="betpawa", marketId="1096755", marketName="Over/Under")
  |                                                             ^^^ NO LINE PASSED
  v
setHistoryDialog({ eventId, marketId, ... })
  |                         ^^^ NO LINE IN STATE
  v
HistoryDialog opened with marketId="1096755"
  |                       ^^^ NO LINE PROP
  v
useOddsHistory({ eventId, marketId: "1096755", bookmakerSlug: "betpawa" })
  |                       ^^^ NO LINE PARAM
  v
api.getOddsHistory({ eventId, marketId: "1096755", bookmakerSlug })
  |                           ^^^ NO LINE IN REQUEST
  v
GET /api/events/{id}/markets/1096755/history?bookmaker_slug=betpawa
  |                                          ^^^ NO LINE QUERY PARAM
  v
SQL: WHERE betpawa_market_id = "1096755"
  |   ^^^ NO LINE FILTER
  v
Returns ALL rows: line=1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5 MIXED TOGETHER
  |
  v
Chart displays nonsensical mixed data from 8 different betting lines
```

---

## Impact

1. **Charts Unreadable:** Over/Under and Handicap history charts mix data from different lines, creating nonsensical visualizations
2. **Margin Calculations Incorrect:** Margins calculated from mixed data are meaningless
3. **User Confusion:** Users see unexpected data when clicking on specific odds badges
4. **Data Integrity Appears Broken:** Users may think the system is storing bad data when actually the query is wrong
5. **Value Detection Useless:** Cannot track odds movement for a specific line to detect value

---

## Proposed Fix (Phase 80)

### 1. Backend: Add Line Query Parameter to API Endpoints

**File:** `src/api/routes/history.py`

Add `line` query parameter to both endpoints:
```python
@router.get("/{event_id}/markets/{market_id}/history")
async def get_odds_history(
    event_id: int,
    market_id: str,
    db: AsyncSession = Depends(get_db),
    bookmaker_slug: str = Query(...),
    line: float | None = Query(default=None, description="Filter by line value"),
    # ... existing params
):
```

Add WHERE clause when line is provided:
```python
if line is not None:
    query = query.where(MarketOdds.line == line)
```

### 2. Frontend: Add Line Prop to HistoryDialog

**File:** `web/src/features/matches/components/history-dialog.tsx`

```typescript
export interface HistoryDialogProps {
  // ... existing props
  line?: number | null  // Add this
}
```

### 3. Frontend: Add Line to useOddsHistory Hook

**File:** `web/src/features/matches/hooks/use-odds-history.ts`

```typescript
export interface UseOddsHistoryParams {
  // ... existing params
  line?: number | null  // Add this
}
```

Include in query key and API call.

### 4. Frontend: Add Line to useMarginHistory Hook

**File:** `web/src/features/matches/hooks/use-margin-history.ts`

Same changes as useOddsHistory.

### 5. Frontend: Add Line to API Client

**File:** `web/src/lib/api.ts`

```typescript
getOddsHistory: (params: {
  // ... existing params
  line?: number | null  // Add this
}) => {
  // Add to searchParams when provided
  if (params.line != null) searchParams.set('line', params.line.toString())
}
```

### 6. Frontend: Update Callers to Pass Line

**File:** `web/src/features/matches/components/market-grid.tsx`

Update `HistoryDialogState` and `handleHistoryClick` to include line.

**File:** `web/src/features/matches/components/match-table.tsx`

Same updates.

---

## Files Requiring Changes (Phase 80)

### Backend
| File | Changes Required |
|------|-----------------|
| `src/api/routes/history.py` | Add `line` query param, add WHERE clause filter |

### Frontend
| File | Changes Required |
|------|-----------------|
| `web/src/features/matches/hooks/use-odds-history.ts` | Add `line` param, include in query key and API call |
| `web/src/features/matches/hooks/use-margin-history.ts` | Add `line` param, include in query key and API call |
| `web/src/features/matches/hooks/use-multi-odds-history.ts` | Add `line` param |
| `web/src/features/matches/hooks/use-multi-margin-history.ts` | Add `line` param |
| `web/src/features/matches/components/history-dialog.tsx` | Add `line` prop, pass to hooks |
| `web/src/lib/api.ts` | Add `line` param to getOddsHistory/getMarginHistory |
| `web/src/features/matches/components/market-grid.tsx` | Pass `line` to HistoryDialog |
| `web/src/features/matches/components/match-table.tsx` | Pass `line` to HistoryDialog |

### No Changes Required
| File | Reason |
|------|--------|
| `src/db/models/odds.py` | Already has `line` column |
| `src/matching/schemas.py` | Already returns `line` in response |

---

## Testing Verification (Phase 80)

1. **API Test:** Call `/api/events/2610/markets/1096783/history?bookmaker_slug=betpawa&line=9.5`
   - Should return only 154 rows (not 770)
   - All rows should have `line=9.5`

2. **UI Test:** Click "Over 9.5 Corners" odds badge
   - Chart should show consistent data for 9.5 line only
   - Title should display "Total Corners Over/Under 9.5"

3. **Margin Test:** Margin calculations should reflect single line data

---

## Priority

**HIGH** - This bug makes historical charts for specifier markets completely unusable. These are frequently viewed markets (Over/Under goals, Asian Handicap) and the broken visualization undermines user trust in the platform.

---

## Investigation Complete

**Investigation Date:** 2026-02-10
**Ready for:** Phase 80 - Specifier Bug Fix
**Status:** Root cause identified, fix approach documented
