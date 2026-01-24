# Phase 16: Cross-Platform Matching Enhancement - Context

**Gathered:** 2026-01-24
**Status:** Ready for research

<vision>
## How This Should Work

The goal is both odds comparison AND coverage gap analysis — seeing which events competitors offer that BetPawa doesn't, alongside comparing odds on matched events.

When the same event exists on multiple platforms, BetPawa's metadata (team names, tournament names) takes priority. Competitors only fill in when BetPawa doesn't have the event.

User wants full stack through UI eventually, but recognizes **matching foundation** is the essential first step. UI can follow quickly after.

**Key insight:** Both `events` and `competitor_events` tables already store `sportradar_id`, so matching might already be possible via JOIN. Phase 16 may be about verifying this works rather than building new matching logic.

</vision>

<essential>
## What Must Be Nailed

- Confirm SportRadar ID matching works across platforms
- Events from BetPawa, SportyBet, and Bet9ja can be connected by shared SportRadar ID
- If matching gaps exist, identify and fix them

</essential>

<boundaries>
## What's Out of Scope

- Historical analysis — comparing how coverage/odds changed over time
- Automated alerts — notifications when competitors add events BetPawa doesn't have
- Market-level comparison — just event-level for now, not detailed market-by-market

</boundaries>

<specifics>
## Specific Ideas

- Filter-based UI approach: filter views by "BetPawa only", "Competitor only", "Both"
- Enhanced Matches page AND new palimpsest comparison page (UI work may be Phase 19-20)

</specifics>

<notes>
## Additional Context

User questioned whether Phase 16 is already complete given that SportRadar ID is stored in both tables. Research needed to verify:
1. Can events be matched via SportRadar ID JOIN today?
2. What percentage of events have valid SportRadar IDs?
3. Are there edge cases (missing IDs, duplicates, etc.) that need handling?

If matching "just works," Phase 16 may be marked complete and focus shifts to Phase 17+ (UI/API work).

</notes>

---

*Phase: 16-cross-platform-matching-enhancement*
*Context gathered: 2026-01-24*
