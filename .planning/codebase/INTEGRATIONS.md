# External Integrations

**Analysis Date:** 2026-01-20

## APIs & External Services

**SportyBet API:**
- Purpose: Extract competitor odds and market data
- Endpoint: `https://www.sportybet.com` - `scraper/src/sportybet_scraper/config.py`
- Client: `scraper/src/sportybet_scraper/client.py`
- Auth: Browser-like headers (User-Agent, clientid, operid, platform)
- Data format: JSON with SportRadar event IDs for cross-platform matching

**BetPawa API:**
- Purpose: Source-of-truth for event discovery and odds extraction
- Endpoint: `https://www.betpawa.ng` - `scraper/src/betpawa_scraper/config.py`
- Client: `scraper/src/betpawa_scraper/client.py`
- Auth: Browser-like headers with brand headers (`x-pawa-brand: betpawa-nigeria`, `devicetype`)
- Data format: JSON with Betpawa event structure - `scraper/src/betpawa_scraper/models.py`

**Bet9ja API:**
- Purpose: Extract competitor odds and market data
- Endpoint: `https://sports.bet9ja.com` - `scraper/src/bet9ja_scraper/config.py`
- Client: `scraper/src/bet9ja_scraper/client.py`
- Auth: Browser-like headers only (no special brand headers)
- Data format: JSON with flattened key-value structure

## Data Storage

**Databases:**
- None - No database integrations

**File Storage:**
- Scraper output: JSON files to local filesystem
- Sample data: `mapping_markets/jsons_examples/`
- Scraper samples: `scraper/responses_examples/`

**Caching:**
- None - No caching layer

## Authentication & Identity

**Auth Provider:**
- None - No user authentication

**API Authentication:**
- All scrapers use browser-like headers
- No API keys or tokens required
- Headers mimic web browser requests

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking (Sentry, etc.)

**Analytics:**
- None - No analytics platform

**Logs:**
- Python scrapers: Structured logging via `logging_config.py`
- Logs to stdout/stderr
- No external log aggregation

## CI/CD & Deployment

**Hosting:**
- Not deployed - Local CLI tools only

**CI Pipeline:**
- None visible - No GitHub Actions or similar

## Environment Configuration

**Development:**
- No environment variables required
- All configuration hardcoded in `config.py` files
- No `.env` files used

**Secrets:**
- No secrets management (no API keys needed)
- Headers are public browser-mimicking values

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Third-Party Data Providers

**SportRadar:**
- Purpose: Cross-platform event identification
- Integration: Event IDs embedded in API responses
- Usage: BetPawa widgets array with `type=SPORTRADAR`
- Location: `mapping_markets/src/types/betpawa.ts`

**Genius Sports:**
- Purpose: Alternative data provider (referenced in widget types)
- Integration: Widget type in BetPawa responses
- Location: `mapping_markets/src/types/betpawa.ts`

## Network Configuration

**HTTP Timeouts:**
- All scrapers: 30 seconds default - `scraper/src/*/config.py`

**Retry Configuration:**
- Max retries: 3 attempts
- Strategy: Exponential backoff with 2x multiplier
- Min wait: 1.0 second
- Max wait: 10.0 seconds
- Implementation: tenacity library - `scraper/src/*/client.py`

**Request Headers (SportyBet):**
```python
{
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "clientid": "2",
    "operid": "1",
    "platform": "web",
    "User-Agent": "Mozilla/5.0 ..."
}
```

**Request Headers (BetPawa):**
```python
{
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "devicetype": "web",
    "user-agent": "Mozilla/5.0 ...",
    "x-pawa-brand": "betpawa-nigeria"
}
```

**Request Headers (Bet9ja):**
```python
{
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "user-agent": "Mozilla/5.0 ..."
}
```

## CLI Commands

**SportyBet Scraper:**
- `sportybet-scraper test-connection` - Connectivity verification
- `sportybet-scraper scrape <event_id>` - Single event extraction
- `sportybet-scraper batch <input_file>` - Batch processing

**BetPawa Scraper:**
- `betpawa-scraper test-connection` - Connectivity verification
- `betpawa-scraper list-sports` - Available sports enumeration
- `betpawa-scraper list-regions <sport_id>` - Region listing
- `betpawa-scraper list-competitions <region_id>` - Competition listing
- `betpawa-scraper list-events <competition_id>` - Event enumeration
- `betpawa-scraper scrape-event <event_id>` - Single event extraction
- `betpawa-scraper pipeline <sport_id>` - Automated end-to-end extraction

**Bet9ja Scraper:**
- `bet9ja-scraper test-connection` - Connectivity verification
- `bet9ja-scraper list-sports` - Available sports enumeration
- `bet9ja-scraper list-groups <sport_id>` - Market groups
- `bet9ja-scraper list-tournaments <sport_id> <group_id>` - Tournament listing
- `bet9ja-scraper list-events <tournament_id>` - Event enumeration
- `bet9ja-scraper scrape-event <event_id>` - Single event extraction
- `bet9ja-scraper pipeline <sport_id>` - Automated end-to-end extraction

## Market Coverage

- **Total mappings**: 111 market configurations
- **Betpawa**: 102 markets (target platform)
- **Sportybet**: 101 markets mapped
- **Bet9ja**: 96 markets mapped
- **Market types**: 1X2, Over/Under, Handicaps, BTTS, Correct Score, Corners, Bookings, Combo markets

---

*Integration audit: 2026-01-20*
*Update when adding/removing external services*
