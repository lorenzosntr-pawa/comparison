# Betpawa Odds Comparison Tool

## What This Is

A comparative analysis tool for Betpawa to analyze and compare its football markets and odds with competitors (SportyBet, Bet9ja). The tool scrapes odds data on a schedule, matches events across platforms using SportRadar IDs, and displays side-by-side comparisons with margin analysis through a React web interface.

## Core Value

Accurate cross-platform market matching and real-time odds comparison that enables Betpawa to understand its competitive position in the Nigerian market.

## Requirements

### Validated

- ✓ Python scrapers for SportyBet, BetPawa, Bet9ja — existing
- ✓ TypeScript market mapping library (111+ markets) — existing
- ✓ Cross-platform event matching via SportRadar IDs — existing

### Active

- [ ] Port TypeScript mapping library to Python
- [ ] FastAPI backend service orchestrating scrapers
- [ ] PostgreSQL database with timestamped odds snapshots
- [ ] Scheduled scraping with configurable interval
- [ ] Event matching by SportRadar ID across all platforms
- [ ] Market mapping for all 111+ supported markets
- [ ] React frontend with match list view (1X2, O/U 2.5, BTTS)
- [ ] Match detail view with all markets (Betpawa grouping)
- [ ] Side-by-side odds display for each market
- [ ] Margin percentage calculation per bookmaker
- [ ] Value delta showing Betpawa vs competitors
- [ ] Color-coded indicators (green/red) for better/worse odds
- [ ] Filtering by league, date/time, margin difference
- [ ] Separate section for unmatched Betpawa events
- [ ] N/A indicators when competitor lacks a market
- [ ] Per-event data freshness timestamps
- [ ] WebSocket real-time updates on new scrape data
- [ ] Silent retry on scraper failures with stale data indication
- [ ] UI banner when data may be stale

### Out of Scope

- User accounts/authentication — internal tool, no access control needed for MVP
- Alerts/notifications to admins — deferred, add after MVP
- Historical trend charts — data stored but visualization deferred
- Data export (CSV/PDF) — view only for MVP
- Sports other than football — focus on football only
- Regions other than Nigeria — Nigeria focus for MVP
- Mobile-first design — desktop-first, basic mobile usability

## Context

**Existing codebase:**
- `mapping_markets/`: TypeScript library for market transformation (111+ market mappings, discriminated unions, Result types)
- `scraper/`: Python CLI tools for SportyBet, BetPawa, Bet9ja with httpx, tenacity retry, Click CLI

**Technical environment:**
- Two-tier architecture currently (Python scrapers + TypeScript library)
- Consolidating to Python backend for simpler deployment
- Zero-dependency TypeScript library makes porting straightforward

**Cross-platform matching:**
- SportRadar event IDs enable reliable cross-platform event matching
- SportyBet: Uses `eventId` directly
- BetPawa: Extracts from `widgets` array with `type=SPORTRADAR`
- Bet9ja: Extracts from `EXTID` field

## Constraints

- **Region**: Nigeria — scrapers configured for Nigerian market APIs
- **Data retention**: 30 days — balance storage costs with analysis needs
- **Match confidence**: SportRadar ID only — no fuzzy name matching

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Port TypeScript mapping to Python | Single-language backend simplifies deployment, avoids inter-service calls | — Pending |
| FastAPI for backend | Modern async Python framework, handles WebSockets, good for scheduled tasks | — Pending |
| PostgreSQL for storage | Robust, handles time-series well, supports complex queries for filtering | — Pending |
| React for frontend | Popular ecosystem, good for data-heavy dashboards | — Pending |
| TanStack Query for state | Server-state focused, handles caching/refetching, pairs well with WebSockets | — Pending |
| Tailwind for styling | Fast prototyping, utility-first, good for MVP speed | — Pending |
| WebSocket for real-time | Push updates immediately when scrape completes, better UX than polling | — Pending |

---
*Last updated: 2025-01-20 after initialization*
