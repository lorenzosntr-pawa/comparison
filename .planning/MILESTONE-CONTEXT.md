# v2.9 Risk Monitoring - Milestone Context

**Created:** 2026-02-19
**Phases:** 105-111 (7 phases)

## Vision

A dedicated **Risk Monitoring** page that surfaces significant odds movements across BetPawa and competitors. Real-time detection of large % changes, direction disagreements, and availability changes with configurable severity thresholds.

## Essential Capabilities

1. **Real-time detection** — Catch movements as they happen via WebSocket
2. **Movement context** — History charts with alert markers
3. **Severity scaling** — Three-tier visual treatment (yellow/orange/red)
4. **Cross-page visibility** — Alert indicators on Odds Comparison/Event Details

## Alert Types

1. **Large % changes** — Odds moved by X% (default: 7%+)
2. **Direction disagreement** — BetPawa vs competitors moving opposite
3. **Availability changes** — Market suspended/returned

## Scope Boundaries

**In scope:**
- Dedicated Risk Monitoring page with tabs (New/Acknowledged/Past)
- Real-time WebSocket updates
- Cross-page alert indicators
- Configurable thresholds and retention

**Out of scope:**
- External notifications (email/SMS/push)
- Automated actions
- In-play monitoring
- Bulk actions

## Phase Mapping

| Phase | Name | Goal |
|-------|------|------|
| 105 | Investigation & Schema Design | Detection patterns, alerts table schema, algorithms |
| 106 | Backend Alert Detection | Detection engine for all three alert types |
| 107 | Alert Storage & API | Database schema, CRUD, API endpoints |
| 108 | Risk Monitoring Page | Table, expandable rows, tabs, filters |
| 109 | Real-Time Updates | WebSocket broadcasting, live updates, sidebar badge |
| 110 | Cross-Page Integration | Indicators on Odds Comparison/Event Details |
| 111 | Settings & Configuration | Thresholds, severity bands, retention settings |

## Detailed Context

See: `.planning/phases/105-investigation-schema/105-CONTEXT.md` for full vision gathered during discuss-phase.
