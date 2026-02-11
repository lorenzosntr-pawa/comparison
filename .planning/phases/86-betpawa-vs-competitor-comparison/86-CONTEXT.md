# Phase 86: Betpawa vs Competitor Comparison - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<vision>
## How This Should Work

The existing cards (tournament cards on Historical Analysis, market cards on Tournament Detail) get enhanced with competitor data displayed alongside Betpawa data. Each card shows columns for each bookmaker — Betpawa | SportyBet | Bet9ja — so you can compare margins at a glance.

A bookmaker selector (toggle buttons in the filter bar) controls which bookmakers appear in the cards. By default all bookmakers are shown. This makes it easy to toggle competitors on/off for focused analysis.

The timeline dialog gets enhanced with competitor lines (stacked on the same chart, each in their own brand color). A separate bookmaker filter within the timeline controls which lines appear. There's also a toggle button in the dialog header to switch between:
- **Overlay view (quick browse)**: Line chart with all selected bookmaker margins over time
- **Difference view (deep analysis)**: Bar chart showing the gap/spread between Betpawa and competitors by time bucket

The goal is to make it obvious where Betpawa stands competitively — whether that's quick visual comparison or drilling into specific time-based patterns.

</vision>

<essential>
## What Must Be Nailed

- **Clear visual comparison** — At a glance, see who's offering better margins and when. No guesswork.
- **Seeing patterns over time** — Identify when/where Betpawa consistently beats or lags competitors (consistent gaps, time windows, market-specific patterns)
- **Actionable insights** — Not just data. Make it obvious what's worth acting on.

</essential>

<boundaries>
## What's Out of Scope

- **Automated alerts** — No notifications when margins diverge. That's a future feature.
- **Statistical analysis** — Keep it visual. No mean/median/stddev calculations.

</boundaries>

<specifics>
## Specific Ideas

**Card Layout:**
- Columns per bookmaker: Betpawa | SportyBet | Bet9ja side by side
- Toggle buttons in filter bar for bookmaker selection
- All bookmakers on by default
- Gray "No data" placeholder when a bookmaker doesn't have data for that event/market
- +/- badge showing Betpawa vs best competitor (quick competitive indicator)
- Progressive loading: show Betpawa immediately, add competitors as they load

**Pages:**
- Both Historical Analysis (tournament cards) and Tournament Detail (market cards) get the bookmaker columns

**Timeline Dialog:**
- Enhance existing TimelineDialog with competitor lines (same dialog, not new)
- Separate bookmaker filter within the timeline (independent from card filter)
- Button in dialog header to toggle between overlay and difference views
- Stacked lines in overlay mode (multi-competitor visible at once)
- Bar chart in difference mode with adaptive time buckets based on data density
- Click-to-lock shows competitors in overlay mode, Betpawa-only in diff mode

**Colors:**
- Fixed brand colors for consistency: Betpawa blue, SportyBet green, Bet9ja orange

**"Better" Definition:**
- Context dependent — lower margin for competitive analysis, higher for profitability. Show both perspectives and let users interpret.

</specifics>

<notes>
## Additional Context

This phase builds heavily on existing infrastructure:
- Cards already show Betpawa margin data (Phase 85.1)
- TimelineDialog already has click-to-lock and time-to-kickoff charts (Phase 81, 85)
- Filter bar patterns exist on Historical Analysis page (Phase 83)

The enhancement is additive — competitor data alongside what's already there, not a redesign.

</notes>

---

*Phase: 86-betpawa-vs-competitor-comparison*
*Context gathered: 2026-02-11*
