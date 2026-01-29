---
phase: 37-event-coordination-layer
plan: 01
subsystem: scraping
tags: [event-coordinator, discovery, priority-queue, async]

# Dependency graph
requires:
  - phase: 36-investigation-architecture-design
    provides: EventCoordinator architecture design

provides:
  - EventTarget, ScrapeBatch, ScrapeStatus data structures
  - EventCoordinator with parallel discovery
  - Priority queue building and batch extraction

affects: [38, 39, 40, 41, 42]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - EventCoordinator for event-centric scraping coordination
    - Priority queue with kickoff urgency + coverage value
    - Parallel discovery with platform-specific semaphore limits

key-files:
  created:
    - src/scraping/schemas/__init__.py
    - src/scraping/schemas/coordinator.py
    - src/scraping/event_coordinator.py

key-decisions:
  - Use dataclass for EventTarget (mutable during scrape cycle)
  - Use StrEnum for ScrapeStatus (DB compatibility)
  - Use TypedDict for ScrapeBatch (simple dict structure)
  - Priority key: (urgency_tier, kickoff, -coverage_count, not_has_betpawa)
  - Urgency tiers: imminent (<30min), soon (30-120min), future (>2hr)
  - Platform semaphores: BetPawa 5, SportyBet 10, Bet9ja 15+25ms delay

patterns-established:
  - EventCoordinator.discover_events() runs parallel discovery
  - EventCoordinator.build_priority_queue() sorts by priority_key
  - EventCoordinator.get_next_batch() returns batch_size events

issues-created: []

# Metrics
duration: 12min
completed: 2026-01-29
---

# Summary

## What Was Built

Created the EventCoordinator class with parallel event discovery and priority queue building. This is the coordination layer for the new event-centric scraping architecture.

### Data Structures (src/scraping/schemas/coordinator.py)

1. **ScrapeStatus** - StrEnum for tracking event lifecycle
   - PENDING, IN_PROGRESS, COMPLETED, FAILED

2. **EventTarget** - Mutable dataclass for events to scrape
   - Properties: sr_id, kickoff, platforms (set), status, results, errors
   - Helper properties: coverage_count, has_betpawa
   - Method: priority_key() for queue ordering

3. **ScrapeBatch** - TypedDict for batch processing
   - Fields: batch_id, events, created_at

### EventCoordinator (src/scraping/event_coordinator.py)

**Discovery Methods:**
- `discover_events()` - Main entry point, runs all platforms in parallel
- `_discover_betpawa()` - Fetches competitions, then events (sem=5)
- `_discover_sportybet()` - Fetches tournaments, then events (sem=10)
- `_discover_bet9ja()` - Fetches sports, then events (sem=15, +25ms delay)

**Queue Methods:**
- `build_priority_queue()` - Sorts events by priority_key()
- `get_next_batch()` - Returns up to batch_size events
- `has_pending_events()` - Check if queue has events
- `get_queue_stats()` - Stats for observability

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 07dcb2d | Create coordinator data structures |
| Task 2+3 | ce51985 | Create EventCoordinator with discovery methods |

## Verification

All verification checks passed:
- [x] Schema imports successfully
- [x] EventCoordinator imports successfully
- [x] priority_key() returns comparable tuples
- [x] No type/syntax errors (py_compile)
- [x] Priority ordering tests pass (imminent > soon > future, 3p > 2p > 1p)

## Ready For

Phase 38 will implement parallel scraping (`scrape_batch()`, `_scrape_event_all_platforms()`) using the EventCoordinator infrastructure built here.
