---
phase: 55-async-write-pipeline
plan: 01
subsystem: database, caching
tags: [alembic, sqlalchemy, change-detection, incremental-upsert]
status: complete
date: 2026-02-05
duration: ~15 minutes
tasks_completed: 2
tasks_total: 2
commits: [abb6245, 689af45]
---

# Phase 55 Plan 01: last_confirmed_at & Change Detection Summary

**Added last_confirmed_at column to snapshot tables and created change detection module enabling incremental upserts that skip unchanged odds data.**

## Performance

- No runtime performance impact from this plan (schema addition + new utility module)
- Change detection comparison is O(n) where n = number of markets per event (~50-200 markets typical)
- Outcome normalisation uses sorted tuples for ordering-independent comparison

## Accomplishments

1. **Added `last_confirmed_at` column** to both `OddsSnapshot` and `CompetitorOddsSnapshot` ORM models as nullable DateTime. Created Alembic migration `i5j1k7l2m6n8` (depends on `h4i0j6k1l4m5`).

2. **Created `src/caching/change_detection.py`** with two functions:
   - `markets_changed(cached_markets, new_markets) -> bool` — compares cached vs scraped market data using normalised outcome comparison (sorted by outcome name to handle ordering differences)
   - `classify_batch_changes(cache, betpawa_snapshots, competitor_snapshots)` — classifies a batch of scraped snapshots into changed (need INSERT) vs unchanged (need `last_confirmed_at` UPDATE), returning existing snapshot IDs for the unchanged set

3. **Exported both functions** from `src/caching/__init__.py` for easy package-level imports.

## Task Commits

| Task | Commit | Message |
|------|--------|---------|
| Task 1 | `abb6245` | feat(55-01): add last_confirmed_at column to snapshot tables |
| Task 2 | `689af45` | feat(55-01): create change detection module for incremental upserts |

## Files Created/Modified

| File | Action |
|------|--------|
| `src/db/models/odds.py` | Modified — added `last_confirmed_at` field, imported `DateTime` |
| `src/db/models/competitor.py` | Modified — added `last_confirmed_at` field, imported `DateTime` |
| `alembic/versions/i5j1k7l2m6n8_add_last_confirmed_at.py` | Created — migration adding column to both tables |
| `src/caching/change_detection.py` | Created — `markets_changed()` and `classify_batch_changes()` |
| `src/caching/__init__.py` | Modified — added exports for new functions |

## Decisions Made

1. **Outcome comparison uses sorted tuples** — outcomes are normalised to `(name, odds, is_active)` tuples sorted by name. This avoids false positives from API responses returning outcomes in different orders between scrape cycles.

2. **Support both ORM objects and dicts as new_markets** — `markets_changed()` accepts either ORM model instances (with attributes) or plain dicts (with keys) for the new markets parameter, using `isinstance(nm, dict)` to branch. This makes the function usable both during scraping (ORM objects) and in tests (dicts).

3. **Assert on unchanged path** — `classify_batch_changes()` uses `assert cached_snap is not None` on the unchanged path because `markets_changed()` always returns True when cached_markets is None, guaranteeing a valid snapshot exists.

## Deviations from Plan

None. Implementation follows the plan exactly.

## Issues Encountered

None. All tasks completed without issues.

## Next Phase Readiness

This plan provides the foundation for Plan 55-02 (async write pipeline) and Plan 55-03 (integration):
- `last_confirmed_at` column is ready for the async writer to UPDATE on unchanged snapshots
- `classify_batch_changes()` is ready to be called by the scraping coordinator to separate changed vs unchanged batches before dispatching to the write queue
- Both functions are importable from `src.caching` package
