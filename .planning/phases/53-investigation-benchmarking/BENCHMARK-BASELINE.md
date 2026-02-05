# Benchmark Baseline Report

**Date:** 2026-02-05 11:45:08 UTC
**Events discovered:** 1291
**Events scraped:** 1291
**Events failed:** 0
**Batches processed:** 26
**Total pipeline time:** 1461515ms (1461.5s)

## Discovery Phase

| Platform | Time (ms) | Events Found |
|----------|-----------|--------------|
| BetPawa  | 17037 | 1121 |
| SportyBet| 18145 | 1276 |
| Bet9ja   | 13339 | 1225 |
| **Total (wall-clock)** | **18187** | **1291 (merged)** |

## Batch Processing

| Metric | Value |
|--------|-------|
| Batch count | 26 |
| Avg batch scrape time (ms) | 34911 |
| Avg batch storage time (ms) | 21298 |
| Storage % of total batch time | 37.9% |
| Scrape % of total batch time | 62.1% |

### Storage Breakdown (avg per batch)

| Sub-phase | Time (ms) | % of Storage |
|-----------|-----------|--------------|
| Lookups | 55 | 0.3% |
| Processing | 7511 | 37.0% |
| Flush | 5713 | 28.1% |
| Commit | 7027 | 34.6% |

## Per-Event Scraping

| Metric | Value |
|--------|-------|
| Avg event scrape time (ms) | 702 |
| P50 event scrape time (ms) | 617 |
| P95 event scrape time (ms) | 1056 |
| Slowest platform (most often) | bet9ja |

### Platform Timing Distribution

| Platform | Avg (ms) | P50 (ms) | P95 (ms) |
|----------|----------|----------|----------|
| Betpawa | 380 | 337 | 517 |
| Sportybet | 589 | 505 | 979 |
| Bet9ja | 641 | 596 | 841 |

## API Response Latency

| Endpoint | P50 (ms) | P95 (ms) |
|----------|----------|----------|
| GET /api/events | 903.1 | 2340.7 |
| GET /api/events/{id} | 35.5 | 37.7 |
| GET /api/scrape/runs | 8.7 | 17.0 |

## Memory

| Metric | Value |
|--------|-------|
| Peak memory (MB) | 2389.48 |
| Memory delta (MB) | 23.45 |

## Bottleneck Analysis

**Dominant cost center:** Scraping

- Discovery: 1.2% of total pipeline time (18187ms)
- Scraping: 61.3% of total pipeline time (907711ms)
- Storage: 37.4% of total pipeline time (553751ms)
- Storage breakdown: Processing dominates (7511ms avg per batch)
- **Recommendation:** Phase 56 (Concurrency Tuning) is highest priority - scraping dominates pipeline time

### Phase Impact Mapping

| v2.0 Phase | Addresses | Current Cost |
|------------|-----------|-------------|
| Phase 54: Cache Layer | API response latency | Measured |
| Phase 55: Async Write Pipeline | Storage bottleneck | 553751ms total |
| Phase 56: Concurrency Tuning | Scraping throughput | 907711ms total |
