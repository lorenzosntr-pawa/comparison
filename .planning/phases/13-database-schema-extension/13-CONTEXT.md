# Phase 13: Database Schema Extension - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<vision>
## How This Should Work

The schema needs to support full competitor palimpsest comparison. When we scrape SportyBet and Bet9ja, we store their tournaments and events in parallel tables — separate from betpawa data but linked via SportRadar IDs for comparison.

The hierarchy should be improved across all platforms: Sport → Region/Country → Tournament → Events. This gives us cleaner organization and enables tournament-level grouping even when SR IDs only exist at event level.

Competitor odds snapshots work just like betpawa snapshots — stored per scrape run, matched by SR ID and time windows. Scrape runs are grouped in batches so we can see "Batch 123: betpawa ✓, sportybet ✓, bet9ja ✗" with clean per-platform logging and error tracking.

When displaying data, the metadata priority chain (betpawa > sportybet > bet9ja) determines which source provides team names, tournament names, and kickoff times.

</vision>

<essential>
## What Must Be Nailed

- **SR ID linkage** — Every competitor event stores SportRadar ID for matching to betpawa events
- **Metadata priority chain** — Schema supports knowing which source (betpawa > sportybet > bet9ja) should provide display metadata
- **Historical tracking** — Odds snapshots + soft deletes to track availability over time (when events disappear matters as much as when they appear)
- **Improved hierarchy** — Sport → Region → Tournament → Events for both betpawa and competitors

</essential>

<boundaries>
## What's Out of Scope

- Actual scraping logic — that's Phase 14-15
- Matching service changes — that's Phase 16
- API endpoints for comparison — that's Phase 18
- Data migration — fresh start, drop existing data and rescrape

</boundaries>

<specifics>
## Specific Ideas

**Table structure:**
- Parallel tables: `competitor_tournaments`, `competitor_events` with `source` column
- SR ID always stored + optional FK to betpawa event when matched (NULL FK = "competitor has this, betpawa doesn't")
- Soft deletes via `deleted_at` timestamp for competitor data

**Markets:**
- Normalized `market_type` enum (using existing market mapping from v1.0)
- Raw `raw_market_name` column for debugging/reference

**Regions/countries:**
- Store both raw platform name and normalized ISO code
- Enables tournament grouping across platforms where SR ID isn't available

**Tournament matching:**
- Event-based linking (if events match by SR ID, their tournaments are implicitly connected)
- Fuzzy name matching for display purposes

**Scrape runs:**
- Grouped/batch approach: each platform has independent runs with own logs/status
- `scrape_batch` table links runs that should be compared together
- Clean error isolation — one platform failing doesn't taint others

**Patterns:**
- Follow existing: SQLAlchemy 2.0 async, Mapped[] columns, Pydantic v2
- Alembic migration (but dropping existing data for fresh start)

</specifics>

<notes>
## Additional Context

This is the foundation phase for v1.1 Palimpsest Comparison. The schema decisions here enable all subsequent phases:
- Phase 14-15: Scraping populates competitor tables
- Phase 16: Matching service updates FKs and links
- Phase 17: Metadata priority queries use source hierarchy
- Phase 18-20: API and UI consume the comparison data

User prioritizes scalability for adding more competitors in the future. Parallel tables + source column approach supports this well.

</notes>

---

*Phase: 13-database-schema-extension*
*Context gathered: 2026-01-23*
