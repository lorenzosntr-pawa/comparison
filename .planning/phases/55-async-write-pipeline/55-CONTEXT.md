# Phase 55: Async Write Pipeline + Incremental Upserts - Context

**Gathered:** 2026-02-05
**Status:** Ready for planning

<vision>
## How This Should Work

Scraping should be completely decoupled from database writes. When a scrape cycle finishes, data goes onto a background queue and scraping can immediately start the next cycle -- it never waits for DB commits.

On the write side, the system should be smart about what it actually persists. If odds haven't changed since the last scrape, don't create a new snapshot row -- just update the "last seen" timestamp so we know the data is fresh. Change detection happens at the per-bookmaker level: if SportyBet's odds changed but Bet9ja's didn't, only write SportyBet's new snapshot. Bet9ja gets a timestamp-only update.

The cache (Phase 54) already serves API reads, so the DB is now primarily for historical record-keeping. This means we can afford to be selective about writes without affecting user experience.

If a write fails, it retries automatically with backoff -- no data loss even under load.

</vision>

<essential>
## What Must Be Nailed

- **Scraping never blocks on DB** -- scraping throughput is completely independent of how fast writes happen
- **Reduced DB volume** -- fewer writes means less DB load, smaller tables, cheaper storage long-term
- **Reliability with retry** -- if a write fails, it retries automatically with no data loss
- **Per-bookmaker change detection** -- only write new snapshots for bookmakers whose odds actually changed; others get timestamp-only update

</essential>

<boundaries>
## What's Out of Scope

- No WebSocket changes -- real-time push to frontend is Phase 57-58, this phase is backend-only pipeline optimization
- No concurrency/parallelism changes -- don't change scraping parallelism limits, that's Phase 56 (Concurrency Tuning)
- No API changes -- cache-first serving from Phase 54 handles reads, this phase is write-path only

</boundaries>

<specifics>
## Specific Ideas

- Change detection compares against what's in the in-memory cache (last known state) to determine if odds have changed
- Per-bookmaker granularity: each bookmaker's snapshot is independently evaluated for changes
- Unchanged bookmakers get timestamp-only updates (last_seen) rather than full snapshot writes
- Queue should handle backpressure gracefully if writes fall behind

</specifics>

<notes>
## Additional Context

Phase 53 baseline showed storage accounts for ~37.4% of pipeline time, with processing and commit sub-phases dominating. Phase 54 already decoupled API reads from DB via caching. This phase completes the picture by decoupling writes.

The combination of async queue + incremental upserts should dramatically reduce the storage bottleneck identified in Phase 53.

</notes>

---

*Phase: 55-async-write-pipeline*
*Context gathered: 2026-02-05*
