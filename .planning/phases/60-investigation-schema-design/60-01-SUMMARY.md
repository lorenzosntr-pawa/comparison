# Phase 60 Plan 01: Investigation & Schema Design Summary

**Current snapshot architecture already supports historical tracking; recommended adding retention configuration and one index for efficient queries.**

## Accomplishments

- **SQL Analysis Complete:** 13 diagnostic queries executed against production database
- **Key Finding:** Multiple snapshots ARE kept per event (avg 52, max 90 over 4 days)
- **Storage Analysis:** ~3.1 MB/event/day at 10-min scrape interval; 18 GB total in 4 days
- **Change Frequency:** 73% of scrape cycles result in new snapshots (odds change frequently)
- **Recommended Strategy:** Option C - Change-based retention (current behavior, no schema overhaul)

## Files Created/Modified

- `.planning/phases/60-investigation-schema-design/DISCOVERY.md` - Full SQL analysis + design recommendations

## Decisions Made

1. **No major schema changes required** - Current architecture with `odds_snapshots` (partitioned) and `market_odds` already stores history
2. **Add `historical_retention_days` setting** - Separate from operational retention to allow extended history
3. **One index addition recommended** - `idx_market_odds_snapshot_market` for efficient trend queries
4. **Storage budget:** 500 events x 90 days = ~139 GB (acceptable with partitioning)

## Key Metrics Discovered

| Metric | Value |
|--------|-------|
| Snapshots in DB | 90,341 |
| Market odds rows | 15.1M |
| Avg markets/snapshot | 167.4 |
| Avg snapshots/event | 51.8 |
| Change rate | 73% |
| Storage/event/day | ~3.1 MB |

## Issues Encountered

None - analysis completed successfully with existing data.

## Next Phase Readiness

- DISCOVERY.md provides complete specification for Phase 61 implementation
- Schema changes minimal (add one setting column)
- Index recommendation ready for migration
- API query patterns documented with example SQL
- Phase 61 can proceed with 5-task implementation outline
