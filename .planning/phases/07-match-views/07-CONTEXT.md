# Phase 7: Match Views - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<vision>
## How This Should Work

A clean, data-dense table showing matched events across all three bookmakers (Betpawa, SportyBet, Bet9ja). The list is filterable by competition and time, sortable by kickoff, margin, or competition. Inline odds comparison shows configurable markets directly in the table — user picks which markets appear via a settings panel (persisted in localStorage).

Each cell shows the odds with color coding: green gradient when Betpawa has better odds, red gradient when worse, neutral when similar. Color intensity scales with margin size — bigger differences show stronger colors.

Clicking a match opens a detail view with:
- **Header**: Teams, kickoff time, competition, and match status (full context)
- **Summary section**: Key markets (1X2, O/U 2.5, BTTS) at the top plus an overall competitive position indicator for Betpawa
- **Full market comparison**: Three columns (one per platform), markets as rows, using Betpawa's groupings and naming as the reference taxonomy
- **Filterable**: Can filter markets by type or group in detail view

Two types of comparison shown:
1. **Per-selection odds comparison** — each individual odd compared across platforms
2. **Per-market margin comparison** — overall margin/overround each bookmaker applies, shown in dedicated column

Missing markets display clearly as dash or N/A — makes gaps obvious rather than hiding incomplete data.

Design is clean and minimal but still data-dense — readability without sacrificing information.

</vision>

<essential>
## What Must Be Nailed

- **Clear margin visibility** — Instantly see where Betpawa is competitive or not vs competitors (Betpawa-centric color coding with gradient intensity)
- **Easy navigation** — Quick filtering by competition and time, multiple sort options (kickoff, margin, competition)
- **Complete market coverage** — Detail view shows ALL mapped markets with both odds AND margin comparison per market

</essential>

<boundaries>
## What's Out of Scope

- Data freshness indicators — deferred to Phase 8 (real-time updates)
- Historical odds trends or movement charts — just current snapshot
- Alerts/notifications when margins change

</boundaries>

<specifics>
## Specific Ideas

- **List view**: Table with configurable inline markets, settings panel for column selection, localStorage persistence
- **Color coding**: Betpawa-centric (green = better, red = worse), gradient intensity based on margin size
- **Detail view**: Platform columns layout, Betpawa-based market groupings/names, filterable by market type
- **Margins**: Separate column for market margins alongside odds columns
- **Summary**: Key markets summary + overall position indicator at top of detail view
- **Missing data**: Show gaps clearly with dash/N/A
- **Filters**: Both competition and time filters essential
- **Sorting**: Multiple options (kickoff, margin, competition)

</specifics>

<notes>
## Additional Context

The comparison serves two purposes:
1. Per-selection comparison — is each individual Betpawa odd better or worse?
2. Per-market margin comparison — how does Betpawa's margin compare to competitors?

Both should be visible to understand Betpawa's competitive position at both granular and market level.

</notes>

---

*Phase: 07-match-views*
*Context gathered: 2026-01-21*
