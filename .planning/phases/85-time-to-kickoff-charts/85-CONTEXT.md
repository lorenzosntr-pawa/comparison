# Phase 85: Time-to-Kickoff Charts - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<vision>
## How This Should Work

Study margin movement from the moment odds are first scraped to as close as possible to kickoff — especially on a tournament level, market by market.

The tournament detail page gets enhanced:
- **Tournament cards**: Show opening margin → closing margin for each of the main 4 markets (1X2, O/U 2.5, BTTS, Double Chance) instead of just an average. This gives immediate insight into direction of movement.
- **Timeline chart moves to dialog**: Instead of sitting at the bottom of the page, the timeline chart opens on-demand in a dialog. Keeps the main page cleaner.

The timeline dialog shows:
- **Per-market charts** with X-axis as **time-to-kickoff** (normalized: -72h, -24h, -1h, etc.) so patterns are comparable across events
- **One tournament average line** per market — shows overall pattern without individual event noise
- **Time bucket zones** visible on the chart: 7+ days, 3-7 days, 24-72h, <24h — see where the biggest margin movements happen
- **Summary stats**: Header with opening→closing margin + delta, plus per-bucket breakdown (avg margin and change within each zone)

Two ways to access the dialog:
1. **From market card**: Each market card has a quick button to open timeline for that specific market
2. **Page-level button**: Opens full multi-market view with tabs/selector for all markets

</vision>

<essential>
## What Must Be Nailed

- **Per-market timeline clarity** — Each market's margin journey from first scrape to kickoff must be crystal clear and easy to read
- **Opening vs closing insight** — The before/after comparison (opening → closing margin) is core insight — cards and dialog should emphasize this
- **Timeframe pattern discovery** — Seeing WHERE in the timeline margins move most is key — time buckets (7+d, 3-7d, 24-72h, <24h) are essential

All three work together — can't prioritize one over others.

</essential>

<boundaries>
## What's Out of Scope

- **Individual event drilldown** — Keep it tournament-level aggregates only, don't add click-through to single event margin history
- **Competitor comparison overlay** — Just Betpawa margins for now — Betpawa vs competitor comparison is Phase 86
- **Export functionality** — No CSV/screenshot export yet — that's Phase 87

</boundaries>

<specifics>
## Specific Ideas

- Time bucket boundaries: **7+ days**, **3-7 days**, **24-72h**, **<24h**
- X-axis: **time-to-kickoff** (normalized across events), not actual timestamps
- Chart line: **tournament average** at each time-to-kickoff point
- Visual style for time buckets: open to whatever works best (shaded zones or divider lines)
- Tournament cards show opening/closing for all **4 main markets** (1X2, O/U 2.5, BTTS, Double Chance)

</specifics>

<notes>
## Additional Context

This phase enhances the existing TournamentDetailPage from Phase 84.2. The current simple timeline chart at the bottom gets replaced with a more powerful dialog-based approach.

The focus is on understanding margin patterns and where the biggest movements occur in the timeline before kickoff. This helps identify if margins typically drop in the final 24h vs earlier in the week.

</notes>

---

*Phase: 85-time-to-kickoff-charts*
*Context gathered: 2026-02-11*
