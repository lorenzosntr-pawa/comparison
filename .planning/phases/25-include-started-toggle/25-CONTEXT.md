# Phase 25: Include Started Toggle - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<vision>
## How This Should Work

When viewing the Coverage Comparison page, in-play/started events are hidden by default. The toggle sits in the header row, right corner near the event count, giving users a clean pre-match view focused on events that haven't started yet.

When users want to see everything, they flip the toggle to include in-play events. The entire page responds — not just the table, but all summary cards update to reflect the filtered state.

</vision>

<essential>
## What Must Be Nailed

- **Clean pre-match view by default** — Hide started events so users can focus on upcoming events for planning purposes
- **Accurate coverage metrics** — All summary cards (match counts, coverage %, gap counts) must correctly reflect the filtered state, not show stale totals

Both are equally important. The filter is useless if the metrics lie.

</essential>

<boundaries>
## What's Out of Scope

- Time-based filtering (no "next 24 hours" or kickoff time filters) — just started vs not started
- Multiple filter presets or saved filter combinations — just one simple toggle
- Complex filter state management — this is a single toggle, not a filter system

</boundaries>

<specifics>
## Specific Ideas

- Toggle placement: top row header, right corner, near the event count display
- Default state: in-play events hidden (toggle off = hide started)
- All cards update dynamically when toggle changes

</specifics>

<notes>
## Additional Context

This complements the country filter added in Phase 24. Together they give users focused views of coverage data — by geography and by event state.

</notes>

---

*Phase: 25-include-started-toggle*
*Context gathered: 2026-01-26*
