# Phase 18: Matches Page Filter + Metadata Priority - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<vision>
## How This Should Work

The Matches page gets a toggle/tabs at the top to switch between views:
- **Main view**: BetPawa-matched events (current behavior) — odds comparison across all platforms
- **Toggle view**: Include competitor-only events — events that exist on SportyBet/Bet9ja but not on BetPawa, showing their odds for comparison

For competitor-only events, display metadata from the best available source (SportyBet preferred, Bet9ja fallback) without showing which source it came from. The events should feel native, not visually different.

This is fundamentally an odds comparison page — the toggle just expands what events are visible for comparison.

</vision>

<essential>
## What Must Be Nailed

- **The filtering itself** — Being able to switch between BetPawa-matched and competitor-only views is the core value of this phase
- **Seamless metadata display** — Competitor events use best-source metadata (sportybet > bet9ja) invisibly

</essential>

<boundaries>
## What's Out of Scope

- **New Palimpsest page** — That's Phase 19, focused on coverage/availability analysis
- **Coverage statistics** — No stats dashboard showing match percentages in this phase
- **Source badges/indicators** — User doesn't need to see which competitor provided the metadata
- **Tournament-level analysis** — This phase is event-level odds comparison only

</boundaries>

<specifics>
## Specific Ideas

- Toggle/tabs at top of Matches page (not a dropdown filter)
- Competitor-only events show up in the same list format as matched events
- Metadata priority: SportyBet > Bet9ja for event names, times, etc.

</specifics>

<notes>
## Additional Context

The Palimpsest page (Phase 19) will handle the "what do competitors offer that we don't" analysis at the tournament/event availability level. This phase keeps the Matches page focused on odds comparison, just with an expanded event set when the toggle is enabled.

</notes>

---

*Phase: 18-matches-page-filter*
*Context gathered: 2026-01-24*
