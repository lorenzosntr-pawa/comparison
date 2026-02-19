# Phase 105: Risk Monitoring - Context

**Gathered:** 2026-02-19
**Status:** Ready for planning

<vision>
## How This Should Work

A dedicated **Risk Monitoring** page that surfaces significant odds movements across BetPawa and competitors. The page is a table of events that have triggered alerts, grouped by event with badge counts showing the number of alerts per event.

When I open Risk Monitoring, I see a clean table with events that have notable odds activity. Each row shows the event (team names), the primary market that moved, the change amount, which bookmaker had the movement, and kickoff time. A badge count shows how many total alerts exist for that event.

Expanding a row reveals the list of individual alerts with "from → to" values and percentage changes, plus competitor odds for the affected market. A button opens the familiar history chart dialog (reusing existing patterns) with vertical marker lines showing exactly when each alert triggered.

The page has three tabs: **New** (unacknowledged alerts), **Acknowledged** (reviewed), and **Past** (post-kickoff events). Alerts automatically move to Past after kickoff.

New alerts appear in real-time via WebSocket, auto-adding to the table with subtle highlighting. The sidebar shows a badge count of unacknowledged alerts.

On Odds Comparison and Event Details pages, events with active alerts show a badge count indicator that links directly to their alert row in Risk Monitoring.

</vision>

<essential>
## What Must Be Nailed

- **Real-time detection** — Catch movements as they happen, not after the fact
- **Movement context** — See the chart history to understand what happened
- **Severity scaling** — Bigger movements = more urgent visual treatment (three-tier: yellow/orange/red)
- **Cross-page visibility** — Alert indicators on Odds Comparison/Event Details linking to Risk Monitoring

</essential>

<boundaries>
## What's Out of Scope

- **External notifications** — No email, SMS, or push alerts; in-app visibility only
- **Automated actions** — No auto-adjusting odds or triggering workflows; pure monitoring
- **In-play monitoring** — Focus on pre-match/upcoming events only
- **Bulk actions** — One-by-one acknowledgment is fine for now

</boundaries>

<specifics>
## Specific Ideas

### Alert Types
Three types of alerts:
1. **Large % changes** — Odds moved by X% within the lookback window (default: 7%+)
2. **Direction disagreement** — BetPawa moved one way while competitors moved opposite
3. **Availability changes** — Market suspended/returned or odds disappeared then reappeared

### Severity Bands (Configurable)
- **Yellow (warning):** 7-10% change
- **Orange (elevated):** 10-15% change
- **Red (critical):** 15%+ change

### Visual Design
- **Color-coded severity** — Red/orange/yellow indicators based on change magnitude
- **Type icons** — Different icons for price change, disagreement, availability alerts
- **Expandable rows** — Click event to see all alerts + competitor odds inline
- **Chart dialog** — Reuse existing HistoryDialog with vertical marker lines at alert points
- **Alert grouping** — Events with multiple movements show badge count, each movement is its own alert

### Row Information
At a glance in each row:
- Event (team names)
- Market + specific outcome (e.g., "1X2 - Home Win")
- Change amount and direction
- Bookmaker source
- Kickoff time
- Detection time (relative, exact on hover)

### Page Features
- **Three tabs:** New / Acknowledged / Past
- **Full filter suite:** Bookmaker, alert type, severity, tournament, country, time range
- **Configurable sorting:** Most recent, severity, kickoff time
- **Per-event mute:** Silence noisy events
- **Live updates:** WebSocket auto-adds new alerts

### Settings
- Quick settings on Risk Monitoring page
- Full configuration on Settings page
- Configurable lookback window
- Configurable alert retention (separate from odds retention)
- Configurable severity threshold bands

### Integration
- **Sidebar:** Top-level nav item + badge count widget
- **Odds Comparison:** Badge count on events with alerts, click links to Risk Monitoring
- **Event Details:** Same badge indicator

### Alert Behavior
- Each significant movement creates its own alert (both kept if same market moves twice)
- Direction disagreement alerts show each bookmaker's direction AND resulting gap
- Availability alerts treated same as price alerts (severity based on timing)

</specifics>

<notes>
## Additional Context

User emphasized wanting all three core capabilities equally: real-time detection, context/history visualization, and severity filtering. This isn't just a notification list — it's a proper monitoring tool.

The feature should feel like a natural extension of the existing app, reusing patterns like HistoryDialog and the filter components. The expandable row pattern keeps the main table scannable while providing depth when needed.

Timestamps use relative time in rows ("5 minutes ago") with exact time on hover/expand for when precision matters.

Charts show vertical marker lines where alerts triggered, visually connecting the timeline to the alert events.

</notes>

---

*Phase: 105-risk-monitoring*
*Context gathered: 2026-02-19*
