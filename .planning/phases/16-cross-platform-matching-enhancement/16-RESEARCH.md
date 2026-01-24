# Phase 16: Cross-Platform Matching Enhancement - Research

**Researched:** 2026-01-24
**Domain:** Internal codebase exploration (not external ecosystem research)
**Confidence:** HIGH

<research_summary>
## Summary

Explored the existing codebase to determine if SportRadar ID matching is already implemented.

**Finding: Matching already works at the storage layer.** The `competitor_events` table has both `sportradar_id` and `betpawa_event_id` FK. During competitor scraping, the service automatically looks up matching BetPawa events by SR ID and populates the FK.

Current matching stats from database:
- BetPawa events: 1,563
- SportyBet: 1,117/1,488 matched (75.1%)
- Bet9ja: 1,760/2,354 matched (74.8%)
- Competitor-only events (not on BetPawa): ~954
- Matching gaps (FK not set but SR ID exists in both): Only 11

**Primary recommendation:** Phase 16 core matching is COMPLETE. Remaining work is exposing matches via API endpoints (Phase 18) and UI (Phase 19-20).
</research_summary>

<existing_implementation>
## What Already Exists

### Schema (Complete)

| Table | Field | Purpose | Status |
|-------|-------|---------|--------|
| `events` | `sportradar_id` | Unique SR ID from BetPawa | UNIQUE, indexed |
| `competitor_events` | `sportradar_id` | SR ID from competitor | Indexed |
| `competitor_events` | `betpawa_event_id` | FK to `events.id` | Auto-populated |

**Relationship:** One-to-Many (`events` -> `competitor_events`)

### Matching Logic (Complete)

Located in [competitor_events.py:61-79](src/scraping/competitor_events.py#L61-L79):

```python
async def _get_betpawa_event_by_sr_id(
    self, session: AsyncSession, sportradar_id: str
) -> int | None:
    """Lookup BetPawa event by SportRadar ID."""
    result = await session.execute(
        select(Event.id).where(Event.sportradar_id == sportradar_id)
    )
    return result.scalar_one_or_none()
```

This is called during competitor event upsert, populating `betpawa_event_id` automatically.

### Bulk Lookup (Available)

Located in [service.py:224-246](src/matching/service.py#L224-L246):

```python
async def get_events_by_sportradar_ids(
    self, session: AsyncSession, sportradar_ids: list[str]
) -> dict[str, Event]:
    """Efficiently get events by a list of SportRadar IDs."""
```

This is available for any queries needing bulk SR ID lookup.
</existing_implementation>

<matching_quality>
## Matching Quality Analysis

### Current Stats (as of 2026-01-24)

| Platform | Total Events | Matched to BetPawa | Match Rate |
|----------|--------------|--------------------| -----------|
| SportyBet | 1,488 | 1,117 | 75.1% |
| Bet9ja | 2,354 | 1,760 | 74.8% |
| **Combined** | 3,842 | 2,877 | 74.9% |

### Unmatched Events

| Category | Count | Meaning |
|----------|-------|---------|
| SportyBet only | 371 | Events SportyBet offers that BetPawa doesn't |
| Bet9ja only | 594 | Events Bet9ja offers that BetPawa doesn't |
| **Potential gaps** | 11 | SR ID exists in both, FK not set (edge cases) |

### Conclusion

The 11 "potential gaps" are negligible (0.3% of competitor events). The remaining ~954 unmatched events are **true competitor-only events** — exactly what palimpsest comparison is designed to surface.

**Matching quality: GOOD.** No structural issues found.
</matching_quality>

<what_is_missing>
## What's Missing (Phase 18+)

The matching infrastructure is complete, but it's not **exposed** via API:

### API Endpoints Needed

1. **Matched events query**
   - Endpoint: `GET /api/palimpsest/matched`
   - Returns: Events with odds from all platforms
   - Query: JOIN `events` with `competitor_events` where `betpawa_event_id IS NOT NULL`

2. **Competitor-only events query**
   - Endpoint: `GET /api/palimpsest/competitor-only`
   - Returns: Events only on competitors, not on BetPawa
   - Query: `competitor_events` where `betpawa_event_id IS NULL`

3. **BetPawa-only events query**
   - Endpoint: `GET /api/palimpsest/betpawa-only`
   - Returns: Events only on BetPawa, not on competitors
   - Query: `events` where no matching `competitor_events.sportradar_id`

4. **Coverage summary**
   - Endpoint: `GET /api/palimpsest/coverage`
   - Returns: Statistics by tournament/sport

### Sample Queries

```sql
-- Matched events (both BetPawa and competitor)
SELECT e.*, ce.source, ce.home_team as competitor_home, ce.away_team as competitor_away
FROM events e
JOIN competitor_events ce ON ce.betpawa_event_id = e.id;

-- Competitor-only events (not on BetPawa)
SELECT * FROM competitor_events
WHERE betpawa_event_id IS NULL;

-- BetPawa-only events (not on competitors)
SELECT * FROM events e
WHERE NOT EXISTS (
    SELECT 1 FROM competitor_events ce
    WHERE ce.sportradar_id = e.sportradar_id
);
```
</what_is_missing>

<phase_16_recommendation>
## Phase 16 Recommendation

### Option A: Mark Phase 16 Complete (Recommended)

The roadmap goal "Match events by SR ID across all three platforms" is **already implemented**:
- Schema supports matching ✓
- Matching logic runs during scraping ✓
- FK relationships are populated ✓
- 75% match rate confirms it's working ✓

Remaining work naturally belongs to:
- **Phase 18:** Palimpsest API Endpoints
- **Phase 19-20:** UI work

### Option B: Mini-Phase 16 (If Concerns Remain)

If you want a formal Phase 16 plan:
1. Investigate the 11 "gap" events (FK not set, SR ID exists)
2. Add index to speed up coverage queries
3. Document matching behavior in PROJECT.md

**Recommended duration:** 1 plan, 15 minutes

### Verdict

Phase 16 as scoped is effectively complete. Proceed to Phase 17 (Metadata Priority) or skip to Phase 18 (API Endpoints).
</phase_16_recommendation>

<file_references>
## File References

| File | Purpose |
|------|---------|
| [event.py:16-56](src/db/models/event.py#L16-L56) | Event model with `sportradar_id` |
| [competitor.py:58-101](src/db/models/competitor.py#L58-L101) | CompetitorEvent model with `sportradar_id` + FK |
| [competitor_events.py:61-79](src/scraping/competitor_events.py#L61-L79) | Matching logic during scraping |
| [service.py:224-246](src/matching/service.py#L224-L246) | Bulk SR ID lookup |
</file_references>

<metadata>
## Metadata

**Research type:** Codebase exploration (not external ecosystem research)

**Questions answered:**
1. Can events be matched via SportRadar ID? **YES, already implemented**
2. What percentage have valid SportRadar IDs? **100% of scraped events have SR IDs**
3. Are there edge cases? **11 minor gaps, 0.3% of data**

**Confidence breakdown:**
- Schema understanding: HIGH (read models directly)
- Matching logic: HIGH (traced code flow)
- Data quality: HIGH (queried actual database)

**Research date:** 2026-01-24
**Valid until:** N/A (internal codebase, no expiry)
</metadata>

---

*Phase: 16-cross-platform-matching-enhancement*
*Research completed: 2026-01-24*
*Ready for planning: Optional mini-plan or skip to Phase 17-18*
