# Phase 12: UI Polish - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<vision>
## How This Should Work

The app should feel clean and professional while being fast and responsive — like a finished product, not a work in progress. No layout shifts, no visual bugs, everything aligned and consistent.

### Dashboard Restructure

The dashboard gets reorganized into three clear tiers:

1. **Top row**: Total Events and Matched Events widgets (keep as-is)

2. **Middle section**: Recent Scrape Runs widget, but with Scrape Interval and Scheduler Status integrated directly into its header. These aren't separate widgets anymore — they're controls embedded in the scrape runs card. Must correctly reflect settings from DB:
   - Scheduler shows "stopped" when disabled in settings
   - Interval matches the value configured in settings
   - Full consistency between what's shown and what's stored

3. **Bottom row**: Single compact status bar combining System Health + Platform Status into one horizontal line showing database status, scheduler status, and platform connection icons (BetPawa, SportyBet, Bet9ja)

### Branding & Navigation

- App renamed to **pawaRisk** everywhere — sidebar, browser tab, any other occurrences
- "Matches" page renamed to **Odds Comparison**

### Scrape Runs Page

Analytics widgets are too prominent for their importance. Shrink them down — just need a quick visual overview of scraping performance, not large charts dominating the page.

### Sidebar

Fix the collapse overlap issue — when sidebar expands or collapses, it currently covers part of the page content. Should work cleanly without overlapping main content. Stays collapsed (icon-only) by default.

</vision>

<essential>
## What Must Be Nailed

- **Dashboard layout** — the three-tier structure with integrated scheduler controls in the scrape runs widget
- **Settings consistency** — scheduler status and interval must correctly reflect DB values at all times
- **Sidebar fix** — no more content overlap when collapsing/expanding
- **pawaRisk branding** — full rebrand across the app

</essential>

<boundaries>
## What's Out of Scope

- No new features — strictly fixing and polishing what exists
- No mobile optimization — desktop focus only
- No redesigns of the overall look — just fixing issues with current design
- No adding functionality to existing widgets/pages

</boundaries>

<specifics>
## Specific Ideas

Dashboard final layout:
```
┌─────────────────────────────────────────────────────┐
│  [Total Events]         [Matched Events]            │  <- Top row
├─────────────────────────────────────────────────────┤
│  Recent Scrape Runs                                 │
│  ┌──────────────────────────────────────────────┐   │
│  │ [Interval: 15m] [Scheduler: Running] (header)│   │  <- Integrated controls
│  │ Run list...                                  │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  [DB: ●] [Scheduler: ●] [BP: ●] [SB: ●] [B9: ●]    │  <- Single status bar
└─────────────────────────────────────────────────────┘
```

Scrape Runs page: Keep analytics but make them compact — small trend indicators rather than large chart panels.

</specifics>

<notes>
## Additional Context

The goal is a polished, professional tool. Current state has visual quirks (sidebar overlap, scattered widgets) that make it feel unfinished. This phase brings it together into a cohesive experience.

Priority on dashboard restructure — that's the main landing page and sets the tone for the whole app.

</notes>

---

*Phase: 12-ui-polish*
*Context gathered: 2026-01-22*
