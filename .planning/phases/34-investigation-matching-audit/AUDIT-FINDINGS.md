# Event Matching Audit Report

**Phase 34: Investigation & Matching Audit**
**Date:** 2026-01-28

---

## Executive Summary

**The event matching system is working correctly.** The perceived 23-26% "unmatched" rate represents competitor-only events that BetPawa genuinely doesn't offer—not matching failures.

**True matching accuracy:**
- SportyBet: **100%** (1668/1668 matchable events linked)
- Bet9ja: **99.9%** (2350/2352 matchable events linked)

**Only 2 events** have a timing-related bug preventing linkage. All other "unmatched" events are competitor-only coverage that BetPawa doesn't have.

**Recommendation:** Minimal fixes needed—one remediation query and optional periodic re-matching job.

---

## 1. Ideal Architecture (How It SHOULD Work)

### Core Matching Principle

All platforms (BetPawa, SportyBet, Bet9ja) provide a **SportRadar ID** for each football event. This is a globally unique identifier issued by SportRadar, a sports data provider. The same match (e.g., "Liverpool vs Manchester United on 2026-02-01") has the same SportRadar ID across all bookmakers who license SportRadar data.

```
┌─────────────────────────────────────────────────────────────────┐
│                    SportRadar Event Universe                     │
│                   (e.g., ID: 61300947)                           │
│                                                                  │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│   │  BetPawa   │    │  SportyBet │    │   Bet9ja   │            │
│   │ sportradar │    │  eventId:  │    │   EXTID:   │            │
│   │ _id:       │    │ sr:match:  │    │ 61300947   │            │
│   │ 61300947   │    │ 61300947   │    │            │            │
│   └────────────┘    └────────────┘    └────────────┘            │
│         │                │                  │                    │
│         └────────────────┼──────────────────┘                    │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  MATCH via SR ID      │                          │
│              │  61300947 = 61300947  │                          │
│              └───────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### Expected Data Flow

1. **Scrape Phase**: Each platform scraped independently
2. **ID Extraction**: Extract numeric SportRadar ID from each platform's format
3. **Normalization**: All IDs stored in same format (e.g., `"61300947"`)
4. **Matching**: Simple string equality on normalized `sportradar_id`
5. **Linkage**: `competitor_events.betpawa_event_id` FK points to matched BetPawa event

### Expected ID Formats

| Platform | API Field | Raw Format | Normalized |
|----------|-----------|------------|------------|
| BetPawa | `widgets[type=SPORTRADAR].id` | `"61300947"` | `"61300947"` |
| SportyBet | `eventId` | `"sr:match:61300947"` | `"61300947"` |
| Bet9ja | `EXTID` | `"61300947"` | `"61300947"` |

After normalization, all three should produce identical `sportradar_id` values, enabling exact-match joins.

---

## 2. Actual Implementation (How It ACTUALLY Works)

### Two Parallel Systems

The codebase has **two distinct scraping approaches** that emerged from v1.1 development:

#### System A: BetPawa-Centric (Legacy, v1.0)

**File:** `src/scraping/orchestrator.py`

- Scrapes BetPawa first → stores in `events` table
- Collects SportRadar IDs from BetPawa scrape
- Passes those IDs to competitor platforms for filtered fetching
- Stores competitor odds in `odds_snapshots` table (keyed to BetPawa events)

#### System B: Full Palimpsest (New, v1.1+)

**File:** `src/scraping/competitor_events.py`

- Scrapes competitor platforms independently (not filtered by BetPawa)
- Stores in separate tables: `competitor_events`, `competitor_odds_snapshots`
- Links to BetPawa via `competitor_events.betpawa_event_id` FK
- Matching happens during scraping in `_upsert_competitor_event()`

### Actual ID Extraction Code

#### BetPawa ([orchestrator.py](src/scraping/orchestrator.py))

```python
def _parse_betpawa_event(self, data: dict) -> dict | None:
    widgets = data.get("widgets", [])
    sportradar_id = None
    for widget in widgets:
        if widget.get("type") == "SPORTRADAR":
            sportradar_id = widget.get("id")  # Raw value, no transformation
            break
```

**Result:** Stores raw value from API (e.g., `"61300947"`)

#### SportyBet ([competitor_events.py:148-168](src/scraping/competitor_events.py#L148-L168))

```python
def _parse_sportybet_event(self, event_data: dict, tournament_id: int) -> dict | None:
    event_id = event_data.get("eventId", "")  # "sr:match:61300947"
    if not event_id.startswith("sr:match:"):
        return None
    sportradar_id = event_id.replace("sr:match:", "")  # "61300947"
```

**Result:** Strips `sr:match:` prefix, stores numeric string (e.g., `"61300947"`)

#### Bet9ja ([competitor_events.py:202-218](src/scraping/competitor_events.py#L202-L218))

```python
def _parse_bet9ja_event(self, event_data: dict, tournament_id: int) -> dict | None:
    ext_id = event_data.get("EXTID")  # Raw value from API
    if not ext_id:
        return None
    return {"sportradar_id": ext_id, ...}  # No transformation
```

**Result:** Stores raw value from API

### Matching Logic ([competitor_events.py:61-79](src/scraping/competitor_events.py#L61-L79))

```python
async def _get_betpawa_event_by_sr_id(
    self, db: AsyncSession, sportradar_id: str
) -> int | None:
    result = await db.execute(
        select(Event.id).where(Event.sportradar_id == sportradar_id)
    )
    row = result.first()
    return row[0] if row else None
```

**Key insight:** Simple string equality comparison—works correctly because all platforms normalize IDs to same format.

---

## 3. Code-Level Issues (Initial Hypotheses)

### ~~BUG-01: Potential ID Format Mismatch~~

**Status:** ❌ **NOT CONFIRMED** - IDs are normalized correctly (see Section 4.3)

### BUG-02: Timing-Dependent Matching

**Status:** ✅ **CONFIRMED** - 2 events affected

**Location:** [competitor_events.py:119](src/scraping/competitor_events.py#L119)

**Description:**
Matching only happens when a competitor event is first scraped. If competitor event scraped BEFORE BetPawa event exists, link is never established even when BetPawa adds the event later.

**Evidence:** 2 Bet9ja events scraped 2026-01-24, BetPawa added same events 2026-01-27—no link created.

### ~~BUG-03: No Re-Matching on Update~~

**Status:** ❌ **NOT A BUG** - Code DOES re-attempt matching on updates (line 129)

### BUG-04: Missing scrape_run_id Linkage (Historical)

**Status:** ✅ **HISTORICAL ONLY** - 8,423 snapshots from 2026-01-24 lack linkage; all data from 2026-01-25+ is 100% linked.

### ~~BUG-05: Dual Scraping Systems Create Confusion~~

**Status:** ❌ **NOT A BUG** - Systems serve different purposes; no data quality impact detected.

---

## 4. Data Analysis (SQL Query Results)

### 4.1 Overall Match Rates

| Source | Total | Matched | Unmatched | Match Rate |
|--------|-------|---------|-----------|------------|
| bet9ja | 3,073 | 2,350 | 723 | 76.47% |
| sportybet | 2,260 | 1,668 | 592 | 73.81% |

**Note:** "Unmatched" includes competitor-only events (no BetPawa equivalent).

### 4.2 Missing Matches Analysis (Events That SHOULD Match)

```sql
SELECT ce.source, COUNT(*) as missing_matches
FROM competitor_events ce
INNER JOIN events e ON ce.sportradar_id = e.sportradar_id
WHERE ce.betpawa_event_id IS NULL AND ce.deleted_at IS NULL
GROUP BY ce.source;
```

**Results:**
- Bet9ja: **2** events with matching SR ID but no link
- SportyBet: **0** events

### 4.3 ID Format Comparison

**Sample IDs from each table:**

| Table | Sample sportradar_id values |
|-------|---------------------------|
| events (BetPawa) | `'61272761'`, `'61272769'`, `'63685097'`, `'67516292'` |
| competitor_events (SportyBet) | `'67912552'`, `'62155300'`, `'63685089'`, `'67546194'` |
| competitor_events (Bet9ja) | `'67697802'`, `'65897796'`, `'62655319'`, `'67681674'` |

**Conclusion:** All IDs are numeric strings with consistent format. No prefix/formatting issues detected.

### 4.4 ID Overlap Analysis

| Metric | Count |
|--------|-------|
| BetPawa unique IDs | 2,218 |
| SportyBet unique IDs | 2,260 |
| Bet9ja unique IDs | 2,014 |
| BetPawa-SportyBet overlap | 1,668 |
| BetPawa-Bet9ja overlap | 1,540 |
| SportyBet-Bet9ja overlap | 1,991 |
| Events on all 3 platforms | 1,535 |

### 4.5 True Match Rate (Matchable Events Only)

**Events where SR ID exists in both tables (should be 100% matched):**

| Source | Should Match | Actually Matched | Broken |
|--------|--------------|------------------|--------|
| sportybet | 1,668 | 1,668 | **0** |
| bet9ja | 2,352 | 2,350 | **2** |

**SportyBet: 100% accurate. Bet9ja: 99.9% accurate.**

### 4.6 scrape_run_id Linkage Pattern

| Day | Total | With Run | Without |
|-----|-------|----------|---------|
| 2026-01-28 | 9,263 | 9,263 | 0 |
| 2026-01-27 | 3,877 | 3,877 | 0 |
| 2026-01-26 | 29,655 | 29,655 | 0 |
| 2026-01-25 | 1,389 | 1,389 | 0 |
| 2026-01-24 | 21,860 | 13,437 | **8,423** |

**Conclusion:** All data from 2026-01-25 onwards has 100% scrape_run_id linkage. The 8,423 missing are historical from day 1.

### 4.7 Team Name "Mismatches" (False Positives)

Sample linked events with different team names:

- SR ID `61272761`: Bet9ja "Puskas Akademia vs Paksi" ↔ BetPawa "Puskas Akademia FC Felcsut vs Paksi FC"
- SR ID `61272765`: Bet9ja "Debreceni vs Diosgyori VTK" ↔ BetPawa "Debreceni VSC vs Diosgyori VTK"

**Conclusion:** These are NOT wrong pairings—same event, different name formatting per platform. Matching is correct.

### 4.8 The 2 Unlinked Events (BUG-02 Evidence)

| SR ID | Competitor Event | BetPawa Event | Timing |
|-------|------------------|---------------|--------|
| 67874330 | "Queens Park - Raith Rovers" (created 2026-01-24) | "Queens Park FC - Raith Rovers FC" (created 2026-01-27) | Competitor BEFORE BetPawa |
| 67874312 | "Inverness - Stenhousemuir" (created 2026-01-24) | "Inverness Caledonian Thistle FC - Stenhousemuir FC" (created 2026-01-27) | Competitor BEFORE BetPawa |

**Root cause confirmed:** Both events were scraped from Bet9ja 3 days before BetPawa added them.

### 4.9 Upcoming Events Match Rates

| Source | Total | Matched | Rate |
|--------|-------|---------|------|
| sportybet | 1,107 | 978 | **88.35%** |
| bet9ja | 1,275 | 1,179 | **92.47%** |

**Note:** The 8-12% unmatched are competitor-only events (legitimate coverage gaps).

---

## 5. Specific Bugs List

### Confirmed Bugs

| ID | Description | Affected | Fix Effort |
|----|-------------|----------|------------|
| BUG-02 | Timing-dependent matching: competitor events scraped before BetPawa exists don't get linked on later scrapes | 2 events | 1 SQL query |

### Non-Issues (Closed)

| ID | Initial Hypothesis | Finding |
|----|-------------------|---------|
| BUG-01 | ID format mismatch | ❌ IDs are consistent across platforms |
| BUG-03 | No re-matching on update | ❌ Code does re-match on update |
| BUG-04 | Missing scrape_run_id | ❌ Historical only (day 1), fixed in code |
| BUG-05 | Dual systems confusion | ❌ Systems work correctly in parallel |

---

## 6. Root Cause Analysis

### Why Does This Appear Broken?

The CONTEXT.md listed symptoms that suggested major matching issues:
- "Missing matches (events exist on all 3 platforms but aren't linked)"
- "Wrong pairings (events matched to wrong counterparts)"

**Reality:**
1. The 23-26% "unmatched" rate is **correct behavior**—those are competitor-only events
2. Team name differences are **normal**—platforms use different naming conventions
3. Only **2 events** (0.06% of Bet9ja data) have actual matching bugs

### The Real Problem

The original hypothesis was based on misinterpreting the data:
- "76% match rate" seemed low
- But 76% of competitor events having BetPawa equivalents is actually **excellent coverage**
- The remaining 24% are events BetPawa simply doesn't offer

### Timing Bug (BUG-02)

The timing issue occurs when:
1. Competitor scrape runs before BetPawa scrape (e.g., new tournament added to competitor first)
2. BetPawa adds the event later
3. On next competitor scrape, the existing record is updated but link attempted again
4. **This actually works!** The code re-attempts matching on update

The 2 affected events are edge cases where:
- They were created on day 1 (2026-01-24)
- BetPawa didn't have them until 3 days later (2026-01-27)
- They haven't been updated since (stale events)

---

## 7. Recommendations

### Immediate Fixes (Phase 35 - Estimated 15 min)

#### Fix 1: One-Time Remediation Query

Run once to fix the 2 broken events:

```sql
UPDATE competitor_events ce
SET betpawa_event_id = e.id
FROM events e
WHERE ce.sportradar_id = e.sportradar_id
  AND ce.betpawa_event_id IS NULL
  AND ce.deleted_at IS NULL;
```

**Impact:** Fixes all current timing-affected events (2 records)

### Optional Enhancements (Phase 36 - if needed)

#### Option A: Periodic Re-Matching Job

Add APScheduler job to run remediation query daily/weekly:

```python
async def rematch_orphaned_events(db: AsyncSession) -> int:
    """Re-attempt matching for competitor events missing betpawa links."""
    result = await db.execute(text("""
        UPDATE competitor_events ce
        SET betpawa_event_id = e.id
        FROM events e
        WHERE ce.sportradar_id = e.sportradar_id
          AND ce.betpawa_event_id IS NULL
          AND ce.deleted_at IS NULL
        RETURNING ce.id
    """))
    count = len(result.fetchall())
    await db.commit()
    return count
```

**Pros:** Catches future timing edge cases automatically
**Cons:** Adds complexity; may not be needed if current fix handles it

#### Option B: Trigger-Based Linking

Add PostgreSQL trigger on `events` table that links matching competitor_events:

```sql
CREATE FUNCTION link_competitor_events() RETURNS TRIGGER AS $$
BEGIN
    UPDATE competitor_events
    SET betpawa_event_id = NEW.id
    WHERE sportradar_id = NEW.sportradar_id
      AND betpawa_event_id IS NULL;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER events_insert_link_competitors
AFTER INSERT ON events
FOR EACH ROW EXECUTE FUNCTION link_competitor_events();
```

**Pros:** Real-time linking, no polling needed
**Cons:** Adds DB-level complexity

### Not Recommended

- **Major refactoring** - The current system works correctly
- **Unified table approach** - Separate tables provide useful data isolation
- **Additional validation layers** - Current matching is accurate

---

## 8. Phase 35-37 Roadmap

Given the minimal issues found, the remaining phases can be simplified:

### Phase 35: Apply Remediation (Single Plan)

- Run one-time remediation query
- Verify 2 affected events are now linked
- Add optional periodic re-matching job if desired

### Phase 36: Coverage Gap Analysis (Optional)

- Analyze which events BetPawa is missing (the 592 SportyBet-only, 723 Bet9ja-only)
- Determine if these represent business opportunities
- This is a business decision, not a technical fix

### Phase 37: Documentation Update (Optional)

- Update architecture docs to clarify dual-system design
- Document ID extraction logic per platform
- Add monitoring for match rate trends

---

## 9. Conclusion

**The event matching system is healthy.** What appeared to be major matching issues are actually:

1. **Correct behavior** - Competitor-only events (24% of data) genuinely don't have BetPawa equivalents
2. **Normal formatting** - Team name differences across platforms are expected
3. **Edge case bug** - Only 2 events affected by timing issue, easily fixed

**Recommended action:** Apply the remediation query (Fix 1) and close this investigation. The system is working as designed.

---

*Report generated: 2026-01-28*
*Phase: 34-investigation-matching-audit*
*Analysis duration: Investigation complete*
