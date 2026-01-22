# Phase 10: Matches Page Improvements - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<vision>
## How This Should Work

The matches page should be a clean, functional table with proper filtering and contextual information visible at a glance. Users need to quickly find matches by team name, competition, or date — and see enough context (region, league, kickoff time) without clicking into each match.

The approach is simple table enhancement rather than complex tree navigation or sportsbook-style collapsible sections. Add columns for missing context and make the filters actually work.

Default sort is by kickoff time (next match first), but users can click column headers to re-sort.

</vision>

<essential>
## What Must Be Nailed

- **Working date filters** — Quick presets (Today, Tomorrow, This Weekend, Next 7 Days) AND a custom date range picker. Currently broken.
- **Team search** — Search input as part of the filter row. Type a team name, find their matches.
- **Competition visibility** — League/competition visible in the table for each match. Region/country also visible.
- **League filter** — Dropdown with search input, scrollable when list is long. Multi-select capable.

All three are equally critical — the page isn't useful until all work together.

</essential>

<boundaries>
## What's Out of Scope

- Saved filters/presets (save "my favorite leagues") — future feature
- Advanced analytics (market coverage stats, odds movement charts) — keep it simple
- Bulk actions (select multiple matches, export data) — not needed now
- Tree-style navigation or collapsible competition sections — simple table approach

</boundaries>

<specifics>
## Specific Ideas

- Simple table approach — add columns and filters to current table, keep it clean
- Date filter: both quick presets AND custom date picker
- Competition dropdown: must be searchable and scrollable
- Team search: part of filter row, not a separate prominent search box
- Default sort by kickoff time, sortable columns via header clicks

</specifics>

<notes>
## Additional Context

This phase focuses on making the matches page functional and informative without overcomplicating the UI. The goal is practical improvements that make finding and comparing matches easier, not building a sophisticated sportsbook-style interface.

</notes>

---

*Phase: 10-matches-page-improvements*
*Context gathered: 2026-01-21*
