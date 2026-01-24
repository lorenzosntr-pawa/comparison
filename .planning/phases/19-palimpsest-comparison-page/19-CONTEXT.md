# Phase 19: Palimpsest Comparison Page - Context

**Gathered:** 2026-01-24
**Status:** Ready for planning

<vision>
## How This Should Work

A new top-level page called "Coverage Comparison" that shows side-by-side views of what tournaments and events each platform has. Three columns: BetPawa | SportyBet | Bet9ja — all visible at once.

Two separate views with equal importance:
1. **Tournament view** — Compare tournament coverage across platforms
2. **Event view** — Compare individual event availability

At the top, summary stat cards show the landscape: coverage percentages, absolute counts, and gap counts. Gap counts should be **per competitor** (not aggregated), because the same missing event might be available on both SportyBet AND Bet9ja.

When a tournament or event is missing from BetPawa but exists on competitors, it appears as a highlighted row inline — gaps are immediately visible, not hidden behind filters.

Clicking a tournament row expands to show its events. Clicking an event row expands for more details.

</vision>

<essential>
## What Must Be Nailed

- **Coverage gaps visible at a glance** — Immediately see which tournaments/events competitors have that BetPawa is missing
- **Market breadth understanding** — See the full scope of what each platform offers
- **Per-competitor gap counts** — Stats show gaps by competitor, not overall totals
- **Three-column layout** — BetPawa | SportyBet | Bet9ja side by side

</essential>

<boundaries>
## What's Out of Scope

- Odds comparison — stays on the existing Matches page, this is purely about coverage/availability
- Historical trend tracking — just current state, not how coverage changes over time
- Export/reports — no CSV exports or downloadable reports for now

</boundaries>

<specifics>
## Specific Ideas

- **Visual indicators** — Color-coded status (green = matched, red/orange = missing)
- **Summary cards at top** — Stats cards showing totals and percentages before detailed lists
- **Filtering options:**
  - Coverage status filter (All / BetPawa has / BetPawa missing)
  - Country/region filter (Nigeria, England, Spain, etc.)
  - Sport filter is lower priority
- **Navigation** — Top-level nav item called "Coverage Comparison" alongside Matches, Scrape Runs
- **Expandable rows** — Click to drill down (tournaments → events, events → details)

</specifics>

<notes>
## Additional Context

This is the final phase of v1.1 Palimpsest Comparison milestone. The page brings together all the competitor data scraped in earlier phases into a dedicated comparison view.

The existing Matches page already has an "All Events" toggle (Phase 18) that shows competitor-only events. This new page focuses on the broader coverage landscape rather than individual match odds.

</notes>

---

*Phase: 19-palimpsest-comparison-page*
*Context gathered: 2026-01-24*
