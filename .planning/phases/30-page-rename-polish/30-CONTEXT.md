# Phase 30: Page Rename & Polish - Context

**Gathered:** 2026-01-26
**Status:** Ready for planning

<vision>
## How This Should Work

A full review pass of the Odds Comparison page before shipping v1.4. This isn't just a quick rename — it's making sure the entire page feels polished and professional after all the restructuring work in Phases 28-29.

The page should be renamed from "Matches" to "Odds Comparison" everywhere: navigation sidebar, page header, and importantly the URL path itself (not just visible text). The table should feel data-dense but clear — maximizing information density while keeping everything readable and scannable.

</vision>

<essential>
## What Must Be Nailed

- **Rename everywhere** — Navigation, page header, AND URL path (e.g., `/matches` → `/odds-comparison`)
- **Scanability** — Quick visual comparison of odds across bookmakers
- **Visual consistency** — Table feels cohesive and professional, not cobbled together

</essential>

<boundaries>
## What's Out of Scope

- No new features — strictly polish what exists
- No new columns, markets, or functionality
- No backend/API changes — frontend only
- Verify URL rename doesn't break any backend API calls or existing links

</boundaries>

<specifics>
## Specific Ideas

- **Data-dense but clear** — maximize information without visual noise
- Polish areas identified:
  - Column widths/spacing — some feel off
  - Visual hierarchy — better separation between matches/markets
  - Color/styling — margin colors, odds highlighting, general refinement
- URL must change, not just display text — check for any deep links or API references

</specifics>

<notes>
## Additional Context

This is the final phase of v1.4 Odds Comparison UX milestone. The table was completely restructured in Phase 28 (bookmakers-as-rows) and Double Chance + margins were added in Phase 29. This phase brings it all together with polish before shipping.

User emphasized verifying the URL rename won't break backend functionality — need to trace any references to the old `/matches` path.

</notes>

---

*Phase: 30-page-rename-polish*
*Context gathered: 2026-01-26*
