# Phase 99.1: Availability Filters

**Status:** Not started
**Milestone:** v2.7 Availability Tracking Bugfix

## Purpose

Add filtering capabilities to show events where bookmakers have stopped offering odds or where markets have been removed. This helps users identify competitive gaps and market availability changes.

## User Request

"We should think on how to add filters to show only events with bookmakers not offering anymore or markets removed"

## Scope (TBD - needs `/gsd:discuss-phase` or `/gsd:research-phase`)

Potential filter options to explore:
- Filter events where a specific bookmaker has unavailable markets
- Filter events where any competitor has removed a market
- Filter events where Betpawa has availability but competitors don't
- Filter markets that recently became unavailable

## Key Files (TBD)

Likely impacted:
- `web/src/features/matches/components/match-table.tsx` - Odds Comparison filters
- `web/src/features/events/components/event-detail.tsx` - Event Details filters
- API endpoints for availability filtering

## Dependencies

- Phase 99: Availability Tracking Fix (provides `unavailable_at` timestamp infrastructure)
- v2.5: Odds Availability Tracking (provides backend availability tracking)

## Next Steps

Run `/gsd:discuss-phase 99.1` to gather requirements and define filter behavior.
