# Phase 6: React Foundation - Context

**Gathered:** 2026-01-20
**Status:** Ready for planning

<vision>
## How This Should Work

A page-based React SPA with four main pages: dashboard/home, match list, match detail, and settings. The app should feel like a professional trading terminal — data-dense but still readable, with a clean modern aesthetic.

The dashboard serves as a command center showing both system health (scheduler status, last scrape times, API health per platform) and quick stats (total matches, coverage across bookmakers).

Navigation uses a collapsible sidebar — full labels when expanded, icons when collapsed to maximize screen real estate for data tables. The match list uses a traditional table layout for maximum density, with side-by-side bookmaker columns (Betpawa | SportyBet | Bet9ja), color-coded best/worst odds, and margins displayed inline.

Settings page provides full scheduler management — pause/resume, interval adjustment, and manual trigger on demand.

Supports both dark and light themes with a toggle for user preference.

</vision>

<essential>
## What Must Be Nailed

- **API integration** - TanStack Query properly wired up, data flowing from backend, loading/error states handled
- **Layout structure** - Collapsible sidebar navigation, page shells, responsive design skeleton
- **Component patterns** - Reusable base components (data tables, cards/panels, status indicators) that Phase 7 builds on

All three must be solid foundations — this phase is about getting the groundwork right so Phase 7 can focus purely on the views.

</essential>

<boundaries>
## What's Out of Scope

- Actual match data display — no real match lists or odds display (that's Phase 7)
- Authentication — this is an internal tool, no login needed
- Mobile optimization — desktop-first, mobile can wait
- Table interactions — sorting, filtering are Phase 7 concerns; just display data for now

</boundaries>

<specifics>
## Specific Ideas

- **Architecture:** Hybrid component structure — shared reusables in `src/components/`, feature-specific in `src/features/`
- **Page structure:** Dashboard, Match List, Match Detail, Settings
- **Navigation:** Collapsible sidebar (full → icon mode)
- **Theme:** Support both dark and light modes with toggle
- **Loading states:** Mix of skeleton loaders and spinners, standard modern patterns
- **Base components:** Data table, card/panel containers, status indicators/badges
- **Comparison display:** Side-by-side bookmaker columns, color-coded best/worst odds (green/red), inline margin percentages

Open to standard modern React tooling choices (router, build tool, component library) — figure out best options during research/planning.

</specifics>

<notes>
## Additional Context

The feel should balance Bloomberg terminal data density with modern design sensibility. Professional and efficient, but not overwhelming.

Dashboard is a command center — system health AND match statistics at a glance.

Settings page should expose full scheduler control (pause/resume, intervals, manual trigger) since this is an internal tool without authentication restrictions.

</notes>

---

*Phase: 06-react-foundation*
*Context gathered: 2026-01-20*
