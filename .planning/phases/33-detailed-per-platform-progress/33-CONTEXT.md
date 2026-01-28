# Phase 33: Detailed Per-Platform Progress Messages - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<vision>
## How This Should Work

During a scrape, the progress view shows each scraping phase (tournament discovery, event scraping, odds fetching) with inline sub-steps per bookmaker. Each phase step expands to show per-bookmaker lines beneath it — for example, "Scraping events" expands to show "SportyBet: 142/200" / "Bet9ja: 89/150" / "BetPawa: 310/310" updating in real time.

The counts are real — actual tournament/event numbers from the scraper, not estimated percentages or generic "processing..." messages. Each platform line also shows elapsed time so you can spot which bookmaker is slow.

</vision>

<essential>
## What Must Be Nailed

- **Real counts, not fake progress** — actual event/tournament counts from the scraper, not estimated percentages or generic messages
- **Per-platform visibility** — see each bookmaker separately so you know which one is slow or failing
- **Timing info** — how long each platform/phase is taking so you can spot performance issues

</essential>

<boundaries>
## What's Out of Scope

- No specific exclusions mentioned — keep it focused on enriching progress events with real per-platform data

</boundaries>

<specifics>
## Specific Ideas

- Inline sub-steps layout: each scraping phase step shows per-bookmaker lines nested beneath it
- Live-updating counters with format like "SportyBet: 142/200 (3.2s)"
- Phase-by-phase breakdown (tournaments, events, odds) rather than one flat progress bar

</specifics>

<notes>
## Additional Context

No additional notes

</notes>

---

*Phase: 33-detailed-per-platform-progress*
*Context gathered: 2026-01-28*
