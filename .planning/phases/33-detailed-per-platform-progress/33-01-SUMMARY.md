---
phase: "33"
plan: "33-01"
subsystem: scraping-progress
tags: [sse, progress, orchestrator, frontend]
requires:
  - Phase 31 heartbeat infrastructure
  - Phase 32 connection loss detection
provides:
  - Per-platform SSE progress events for sportybet and bet9ja
  - Real event counts and duration timing in live progress UI
affects:
  - src/scraping/orchestrator.py
  - web/src/features/scrape-runs/components/live-progress.tsx
tech-stack: [FastAPI, SSE, React 19, TypeScript]
key-files:
  - src/scraping/orchestrator.py
  - web/src/features/scrape-runs/components/live-progress.tsx
key-decisions:
  - Emit per-platform SCRAPING/COMPLETED/FAILED events inside existing competitor phase rather than restructuring phases
  - Keep overall competitor COMPLETED event as phase-level marker alongside new per-platform events
  - Show "scraping..." for active platforms instead of adding a live timer (avoids setInterval complexity)
  - Preserve existing progress bar width logic (60% for active) since real improvement is counts and timing
metrics:
  duration: ~8 minutes
  task-count: 2
  file-count: 2
---

# 33-01 Summary: Per-platform SSE progress events with real event counts and duration timing

## Accomplishments

- Backend orchestrator now emits individual SCRAPING and COMPLETED/FAILED events for SportyBet and Bet9ja during the competitor phase, each with platform-specific timing and event counts
- Frontend live progress panel displays real per-platform data: completed platforms show "{count} events ({duration}s)", active platforms show "scraping...", pending show "pending"
- Added `durationMs` and `startedAt` tracking to PlatformProgress interface for accurate per-platform state

## Task Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b70d8fd | Emit per-platform progress events for sportybet and bet9ja |
| 2 | 9235718 | Display per-platform event counts and duration in live progress |

## Files Modified

- `src/scraping/orchestrator.py` — Added per-platform SCRAPING/COMPLETED/FAILED event emission around each competitor scrape
- `web/src/features/scrape-runs/components/live-progress.tsx` — Extended ScrapeProgressEvent and PlatformProgress interfaces, updated display logic for real counts and timing

## Decisions Made

1. **Per-platform events inside existing phase**: Rather than creating new phases, emit platform-specific events within the existing competitor phase block. The overall competitor COMPLETED event remains as the phase-level marker.
2. **No live timer**: Active platforms show "scraping..." text rather than a ticking elapsed counter, avoiding setInterval complexity for minimal UX gain.
3. **Schema unchanged**: All needed fields (platform, duration_ms, elapsed_ms, events_count) already existed on ScrapeProgress.

## Deviations

None.

## Issues

None.

## Next Phase Readiness

Ready. Per-platform progress infrastructure is in place for any future enhancements like storing/mapping sub-phases or expanding to additional competitor platforms.
