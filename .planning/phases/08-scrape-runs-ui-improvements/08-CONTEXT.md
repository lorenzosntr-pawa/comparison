# Phase 8: Scrape Runs UI Improvements - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<vision>
## How This Should Work

The scrape runs experience should be comprehensive — combining live progress, historical analytics, and actionable monitoring into one cohesive system.

**On the dedicated Scrape Runs page:**
- Detailed per-platform progress bars showing each bookmaker (Betpawa, SportyBet, Bet9ja) progressing independently with event counts and timing
- Rich breakdown of what's happening during active scrapes
- Historical analytics showing trends over time

**On the dashboard widget:**
- Simplified overall progress indicator — one main bar showing total scrape progress
- Quick status at a glance without needing to navigate to the full page

**Analytics should show:**
- Scrape duration trends (line charts showing speed over days/weeks)
- Success/failure rates (reliability patterns by platform)
- Event counts over time (tracking capture volume)

**For problem handling:**
- Detailed error messages and logs when scrapes fail
- Platform-specific retry — ability to retry just the failed platform(s), not the whole run

The overall feel should stay clean and card-based, consistent with the existing dashboard style. Not data-dense like Grafana — focused and minimal.

</vision>

<essential>
## What Must Be Nailed

- **Live progress visibility** — Detailed per-platform progress on dedicated page, overall summary in widget
- **Historical analytics** — Duration trends, success rates, event counts over time
- **Problem resolution** — Clear error details and ability to retry specific failed platforms

All three are equally important for the tool to feel complete and useful.

</essential>

<boundaries>
## What's Out of Scope

- Notifications/alerts (no email/SMS/push when scrapes fail — UI monitoring only)
- Automatic retry logic is in scope (manual platform-specific retry is desired)

</boundaries>

<specifics>
## Specific Ideas

- Per-platform progress bars with independent event counts on Scrape Runs page
- Single overall progress bar in dashboard widget
- Clean, card-based layout consistent with existing UI
- Platform-specific retry buttons (not whole-run retry)
- Error details visible for troubleshooting

</specifics>

<notes>
## Additional Context

This phase builds on the scrape runs UI foundation from Phase 7.2, which already includes:
- Scrape runs history page
- Scrape run detail view with platform breakdown
- Recent runs widget on dashboard
- SSE streaming for real-time progress

The goal is to enhance these existing pieces with better live visualization, analytics, and actionable error handling.

</notes>

---

*Phase: 08-scrape-runs-ui-improvements*
*Context gathered: 2026-01-21*
