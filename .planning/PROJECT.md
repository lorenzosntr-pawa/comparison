# Betpawa Odds Comparison Tool

## What This Is

A comparative analysis tool (branded "pawaRisk") for Betpawa to analyze and compare its football markets and odds with competitors (SportyBet, Bet9ja). The tool scrapes odds data on a schedule, matches events across platforms using SportRadar IDs, and displays side-by-side comparisons with margin analysis through a React web interface.

## Core Value

Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.

## Current State (v1.0 MVP)

**Shipped:** 2026-01-23

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL
- Frontend: React 19, Vite, TanStack Query v5, Tailwind CSS v4, shadcn/ui
- 18,595 lines of code

**Capabilities:**
- 108 market mappings from SportyBet and Bet9ja to Betpawa format
- Cross-platform event matching via SportRadar IDs
- Automated scraping with configurable intervals
- Real-time progress streaming via SSE
- Dashboard with scheduler controls, platform health, and analytics
- Match list and detail views with color-coded odds comparison

## Requirements

### Validated

- ✓ Port TypeScript mapping library to Python — v1.0
- ✓ FastAPI backend service orchestrating scrapers — v1.0
- ✓ PostgreSQL database with timestamped odds snapshots — v1.0
- ✓ Scheduled scraping with configurable interval — v1.0
- ✓ Event matching by SportRadar ID across all platforms — v1.0
- ✓ Market mapping for 108 supported markets — v1.0
- ✓ React frontend with match list view (1X2, O/U 2.5, BTTS) — v1.0
- ✓ Match detail view with all markets (Betpawa grouping) — v1.0
- ✓ Side-by-side odds display for each market — v1.0
- ✓ Margin percentage calculation per bookmaker — v1.0
- ✓ Value delta showing Betpawa vs competitors — v1.0
- ✓ Color-coded indicators (green/red) for better/worse odds — v1.0
- ✓ Filtering by league, date/time — v1.0
- ✓ N/A indicators when competitor lacks a market — v1.0
- ✓ Per-event data freshness timestamps — v1.0

### Active

- [ ] WebSocket real-time updates on new scrape data
- [ ] Unmatched events section for Betpawa-only events
- [ ] Silent retry on scraper failures with stale data indication
- [ ] UI banner when data may be stale

### Out of Scope

- User accounts/authentication — internal tool, no access control needed
- Alerts/notifications to admins — deferred, add after MVP
- Historical trend charts — data stored but visualization deferred
- Competitor event import — removed from roadmap, deprioritized
- Data export (CSV/PDF) — view only for now
- Sports other than football — focus on football only
- Regions other than Nigeria — Nigeria focus
- Mobile-first design — desktop-first, basic mobile usability

## Context

**Existing codebase:**
- `src/market_mapping/`: Python library for market transformation (108 mappings)
- `src/scraping/`: Async clients for SportyBet, BetPawa, Bet9ja
- `src/api/`: FastAPI backend with scheduler and SSE streaming
- `web/`: React frontend with TanStack Query and shadcn/ui

**Technical decisions:**
- Betpawa is canonical format — competitors mapped to Betpawa taxonomy
- SportRadar IDs enable reliable cross-platform matching
- SSE streaming for scrape progress (WebSocket deferred)
- structlog for structured logging with JSON/console modes

## Constraints

- **Region**: Nigeria — scrapers configured for Nigerian market APIs
- **Data retention**: 30 days — balance storage costs with analysis needs
- **Match confidence**: SportRadar ID only — no fuzzy name matching

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Port TypeScript mapping to Python | Single-language backend simplifies deployment | ✓ Good — 108 mappings working |
| FastAPI for backend | Modern async Python framework, handles SSE well | ✓ Good — clean architecture |
| PostgreSQL for storage | Robust, handles time-series well, supports complex queries | ✓ Good — performant |
| React for frontend | Popular ecosystem, good for data-heavy dashboards | ✓ Good — maintainable |
| TanStack Query for state | Server-state focused, handles caching/refetching | ✓ Good — reduced boilerplate |
| Tailwind for styling | Fast prototyping, utility-first | ✓ Good — consistent styling |
| SSE for real-time | Simpler than WebSocket for one-way streaming | ✓ Good — works well for progress |
| StrEnum for status fields | Type safety + string storage in DB | ✓ Good — clean enums |
| Betpawa-first metadata | Competitors insert-only except kickoff | ✓ Good — consistent data |

---
*Last updated: 2026-01-23 after v1.0 milestone*
