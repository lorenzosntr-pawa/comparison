# Phase 4: Event Matching Service - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<vision>
## How This Should Work

When events are scraped, they automatically link to existing events with the same SportRadar ID — no manual intervention needed. Since all three bookmakers (SportyBet, BetPawa, Bet9ja) use SportRadar as their data provider, every event should have a SportRadar ID.

The result is a unified event record: one canonical event with odds from all available platforms attached. This enables side-by-side odds comparison, finding best prices, and margin analysis across platforms.

**Betpawa-centric approach:** Since this tool is for Betpawa, event metadata (tournament names, competition structure, team names) should reflect Betpawa's data. Competitor platforms provide their odds, but Betpawa's naming is the source of truth.

**Coverage gaps:** If an event exists on competitors but NOT on Betpawa, store competitor metadata so you can still see what competitors are offering that Betpawa isn't covering. This surfaces valuable intelligence about market gaps.

</vision>

<essential>
## What Must Be Nailed

- **Accuracy AND coverage** — Link as many events as possible while never incorrectly linking different matches. SportRadar IDs make this achievable since they're exact identifiers.
- **Real-time matching** — Events match during scrape, not as a separate batch process. Data is ready for comparison immediately.
- **Partial matches are valid** — If an event appears on 2 platforms, show the comparison with available odds and indicate which platform is missing.
- **Historical snapshots** — Store multiple odds snapshots over time (not just latest) for tracking market movements.

</essential>

<boundaries>
## What's Out of Scope

- **Fuzzy matching** — No team name matching or date-based guessing. Only exact SportRadar ID matches.
- **UI for matches** — This is backend service only. Comparison views come in Phase 7.
- **Non-football sports** — Focus on football first where volume is highest. Matching logic is generic but testing/focus is football.

</boundaries>

<specifics>
## Specific Ideas

- **Betpawa metadata priority**: Use Betpawa's tournament/team names as canonical. Only use competitor metadata when Betpawa doesn't have the event.
- **Unmatched events endpoint**: Include an endpoint to see unmatched events for monitoring data quality and coverage gaps.
- **Flexible filtering**: Support queries by competition, time (upcoming/live/today), and platform coverage (all 3 vs partial).
- **Market normalization**: Store both original platform market names AND normalized market IDs (from Phase 1) for flexibility.
- **Single-platform events**: Still display events that only appear on one platform — they might match later or show coverage gaps.
- **Missing SportRadar ID**: Flag as anomaly (shouldn't happen since all use SportRadar), but don't design complex handling around it.

</specifics>

<notes>
## Additional Context

The primary use cases for matched events are:
1. Side-by-side odds comparison for same markets
2. Quickly identifying which platform has best price
3. Comparing bookmaker margins on same events

All three feed into Betpawa understanding their competitive position in the Nigerian market.

</notes>

---

*Phase: 04-event-matching*
*Context gathered: 2026-01-20*
