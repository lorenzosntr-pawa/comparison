# Pipeline Benchmark Report (Phase 56: Concurrency Tuning)

**Date:** 2026-02-05 16:36:44 UTC
**Events discovered:** 1311
**Events scraped:** 1311
**Events failed:** 0
**Batches processed:** 27
**Total pipeline time:** 508604ms (508.6s)
**Effective throughput:** 2.6 events/second
**Async write queue:** Active

## Concurrency Configuration

| Parameter | Value |
|-----------|-------|
| max_concurrent_events | 10 |
| batch_size | 50 |
| betpawa_concurrency | 50 |
| sportybet_concurrency | 50 |
| bet9ja_concurrency | 15 |
| HTTP max_connections | 200 |
| HTTP max_keepalive | 100 |

## Discovery Phase

| Platform | Time (ms) | Events Found |
|----------|-----------|--------------|
| BetPawa  | 16910 | 1127 |
| SportyBet| 17181 | 1303 |
| Bet9ja   | 12738 | 1214 |
| **Total (wall-clock)** | **17208** | **1311 (merged)** |

## Batch Processing

| Metric | Value |
|--------|-------|
| Batch count | 27 |
| Avg batch scrape time (ms) | 11482 |
| Avg batch storage time (ms) | 7352 |
| Storage % of total batch time | 39.0% |
| Scrape % of total batch time | 61.0% |

### Batch Scrape Time Distribution

| Metric | Value (ms) |
|--------|------------|
| Min | 4648 |
| Avg | 11482 |
| P50 | 10707 |
| P95 | 18245 |
| Max | 22735 |

### Storage Breakdown (avg per batch)

| Sub-phase | Time (ms) | % of Storage |
|-----------|-----------|--------------|
| Lookups | 49 | 0.8% |
| Processing | 5782 | 98.6% |
| Flush | 0 | 0.0% |
| Commit | 35 | 0.6% |
| Change Detection | 405 | new |
| Queue Enqueue | 0 | new |
| Cache Update | 278 | new |

## Per-Event Scraping

| Metric | Value |
|--------|-------|
| Avg event scrape time (ms) | 2180 |
| P50 event scrape time (ms) | 1307 |
| P95 event scrape time (ms) | 6351 |
| Slowest platform (most often) | bet9ja |

### Platform Timing Distribution

| Platform | Avg (ms) | P50 (ms) | P95 (ms) |
|----------|----------|----------|----------|
| Betpawa | 1259 | 622 | 3997 |
| Sportybet | 1475 | 971 | 4065 |
| Bet9ja | 2117 | 1201 | 6299 |

## Async Write Pipeline (Phase 55)

| Metric | Baseline (Phase 53) | After Phase 55 | Change |
|--------|---------------------|----------------|--------|
| Storage blocking time (avg/batch) | 21298ms | 7352ms | +65.5% |
| Snapshots created per cycle | ~3900 | 3644 | async+change-detect |
| Write queue drain time | N/A | 120ms | new |
| Avg change detection (ms/batch) | N/A | 405ms | new |
| Avg queue enqueue (ms/batch) | N/A | 0ms | new |
| Avg cache update (ms/batch) | N/A | 278ms | new |

**Key improvement:** Storage no longer blocks the scraping pipeline. The coordinator
updates the cache immediately and enqueues changed data for background DB writes.
Unchanged snapshots get a `last_confirmed_at` timestamp update instead of full INSERT.

## Concurrency Tuning (Phase 56)

| Metric | Baseline (Phase 53) | After Phase 56 | Change |
|--------|---------------------|----------------|--------|
| Avg batch scrape time | 34911ms | 11482ms | +67.1% |
| Total pipeline time | 1461515ms (1462s) | 508604ms (509s) | +65.2% |
| Throughput (events/sec) | 0.9 | 2.6 | +191.8% |
| max_concurrent_events | 1 (sequential) | 10 | new |
| HTTP max_connections | 100 | 200 | +100% |

**Key improvement:** Events within each batch are now scraped concurrently
(up to 10 at a time) instead of sequentially. Per-platform
semaphores throttle load to prevent rate limiting while maximizing throughput.

## API Response Latency

| Endpoint | P50 (ms) | P95 (ms) |
|----------|----------|----------|
| GET /api/events | 35.9 | 248.6 |
| GET /api/events/{id} | 37.5 | 51.4 |
| GET /api/scrape/runs | 18.4 | 50.6 |

## Memory

| Metric | Value |
|--------|-------|
| Peak memory (MB) | 3153.70 |
| Memory delta (MB) | 46.56 |

## Bottleneck Analysis

**Dominant cost center:** Scraping

- Discovery: 3.3% of total pipeline time (17208ms)
- Scraping: 59.0% of total pipeline time (310031ms)
- Storage: 37.8% of total pipeline time (198521ms)
- Storage breakdown: Processing dominates (5782ms avg per batch)
- **Recommendation:** Scraping still dominates - consider increasing max_concurrent_events or platform concurrency

### Phase Impact Mapping

| v2.0 Phase | Addresses | Status |
|------------|-----------|--------|
| Phase 54: Cache Layer | API response latency | Measured |
| Phase 55: Async Write Pipeline | Storage bottleneck | 198521ms total |
| Phase 56: Concurrency Tuning | Scraping throughput | 310031ms total (+67.1% vs baseline) |
