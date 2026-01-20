# Phase 3: Scraper Integration - Research

**Researched:** 2026-01-20
**Domain:** FastAPI service integrating existing sync scrapers with async concurrency
**Confidence:** HIGH

<research_summary>
## Summary

Researched patterns for integrating three existing synchronous httpx-based scrapers (SportyBet, BetPawa, Bet9ja) into a FastAPI orchestration service. The scrapers already have robust implementations with tenacity retry logic and dataclass models.

Key decision: Convert scrapers from sync to async httpx clients rather than wrapping sync code in `run_in_executor`. HTTPX AsyncClient provides true async I/O, better connection pooling, and is the recommended approach for FastAPI applications. The conversion is straightforward since HTTPX's sync and async APIs are nearly identical.

For concurrent execution with partial failure tolerance (a key requirement), use `asyncio.gather(return_exceptions=True)` which collects all results including exceptions without stopping other coroutines.

**Primary recommendation:** Convert existing sync scrapers to async, use FastAPI lifespan for client management, and use `asyncio.gather(return_exceptions=True)` for concurrent scraping with partial failure handling.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | >=0.109 | Web framework | Async-first, automatic OpenAPI docs, Pydantic integration |
| httpx | >=0.27 | HTTP client | Async support, requests-like API, already used in scrapers |
| tenacity | >=8.2 | Retry logic | Already used in scrapers, works with async |
| pydantic | >=2.10 | Validation | Already in project, FastAPI integration |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uvicorn | >=0.27 | ASGI server | Running the FastAPI app |
| python-multipart | >=0.0.6 | Form data | If form uploads needed (optional) |

### Already Available (from existing packages)
| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| sqlalchemy[asyncio] | >=2.0 | Database ORM | Already configured in src/db |
| asyncpg | >=0.29 | PostgreSQL driver | Already configured |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| asyncio.gather | asyncio.TaskGroup (3.11+) | TaskGroup cancels all on first failure; gather with return_exceptions=True allows partial success |
| httpx AsyncClient | aiohttp | aiohttp slightly faster but different API; httpx already used in project |
| run_in_executor | AsyncClient conversion | run_in_executor is simpler migration but worse performance and no connection pooling |

**Installation:**
```bash
pip install "fastapi>=0.109" "uvicorn[standard]>=0.27"
# httpx, tenacity, pydantic already available
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI app factory + lifespan
│   ├── dependencies.py     # Shared dependencies (db session, etc.)
│   └── routes/
│       ├── __init__.py
│       ├── health.py       # Health/status endpoints
│       └── scrape.py       # Scrape orchestration endpoints
├── scraping/
│   ├── __init__.py
│   ├── clients/            # Async scraper clients (converted from sync)
│   │   ├── __init__.py
│   │   ├── base.py         # Base async client protocol
│   │   ├── sportybet.py    # Async SportyBet client
│   │   ├── betpawa.py      # Async BetPawa client
│   │   └── bet9ja.py       # Async Bet9ja client
│   ├── orchestrator.py     # Coordinates multiple scrapers
│   └── schemas.py          # Scraping-specific Pydantic models
├── db/                     # (already exists)
└── market_mapping/         # (already exists)
```

### Pattern 1: FastAPI Lifespan for Async Clients
**What:** Initialize shared AsyncClient instances at startup, close at shutdown
**When to use:** Always - avoids creating new clients per request
**Example:**
```python
from contextlib import asynccontextmanager
from typing import AsyncIterator, TypedDict
import httpx
from fastapi import FastAPI

class AppState(TypedDict):
    sportybet_client: httpx.AsyncClient
    betpawa_client: httpx.AsyncClient
    bet9ja_client: httpx.AsyncClient

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[AppState]:
    # Create clients with platform-specific config
    async with (
        httpx.AsyncClient(base_url="https://www.sportybet.com", ...) as sporty,
        httpx.AsyncClient(base_url="https://www.betpawa.ng", ...) as betpawa,
        httpx.AsyncClient(base_url="https://web.bet9ja.com", ...) as bet9ja,
    ):
        yield {
            "sportybet_client": sporty,
            "betpawa_client": betpawa,
            "bet9ja_client": bet9ja,
        }

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: Concurrent Scraping with Partial Failure Tolerance
**What:** Run all scrapers concurrently, collect results including failures
**When to use:** When scraping multiple platforms where one failing shouldn't stop others
**Example:**
```python
import asyncio
from dataclasses import dataclass

@dataclass
class ScrapeResult:
    platform: str
    events: list[dict] | None
    error: Exception | None = None

async def scrape_all(clients: dict) -> list[ScrapeResult]:
    tasks = [
        scrape_sportybet(clients["sportybet"]),
        scrape_betpawa(clients["betpawa"]),
        scrape_bet9ja(clients["bet9ja"]),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [
        ScrapeResult(
            platform=platform,
            events=result if not isinstance(result, Exception) else None,
            error=result if isinstance(result, Exception) else None,
        )
        for platform, result in zip(["sportybet", "betpawa", "bet9ja"], results)
    ]
```

### Pattern 3: Async Tenacity Retry
**What:** Use tenacity decorators with async functions
**When to use:** For API calls that need retry logic
**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
)
async def fetch_event(client: httpx.AsyncClient, event_id: str) -> dict:
    response = await client.get(f"/api/event/{event_id}")
    response.raise_for_status()
    return response.json()
```

### Pattern 4: Request-Level Timeout Override
**What:** Allow per-request timeout configuration via query params
**When to use:** When API consumers need flexibility
**Example:**
```python
from fastapi import Query

@router.post("/scrape")
async def scrape_events(
    request: Request,
    timeout: int = Query(default=30, ge=5, le=300, description="Timeout per scraper in seconds"),
):
    # Override client timeout for this request
    async with httpx.AsyncClient(timeout=timeout) as client:
        # ... or pass timeout to each scraper call
```

### Anti-Patterns to Avoid
- **Creating new AsyncClient per request:** Loses connection pooling benefits
- **Using sync httpx in async endpoints:** Blocks the event loop
- **asyncio.TaskGroup for partial failure scenarios:** Cancels all tasks on first exception
- **Ignoring return value types from gather(return_exceptions=True):** Must check isinstance(result, Exception)
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP retry logic | Custom retry loops | tenacity | Already battle-tested, configurable, async-compatible |
| Response validation | Manual dict checking | Pydantic models | Automatic validation, serialization, documentation |
| Concurrent execution | Manual task management | asyncio.gather | Handles task collection, exception aggregation properly |
| Client lifecycle | Manual open/close | FastAPI lifespan + context managers | Ensures proper cleanup, async context handling |
| API documentation | Manual OpenAPI spec | FastAPI response_model | Auto-generated from Pydantic models |

**Key insight:** The existing scrapers already have well-implemented tenacity retry logic and validation. The main work is converting from sync to async httpx and wrapping with FastAPI orchestration - not reimplementing the core scraping logic.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Blocking the Event Loop with Sync Code
**What goes wrong:** Using sync httpx Client in async endpoint freezes other requests
**Why it happens:** Sync I/O blocks the entire async event loop
**How to avoid:** Convert to AsyncClient - the API is nearly identical
**Warning signs:** High latency on concurrent requests, "event loop blocked" warnings

### Pitfall 2: Not Closing Async Clients Properly
**What goes wrong:** Resource leaks, unclosed connection warnings in tests
**Why it happens:** AsyncClient needs explicit aclose() or context manager
**How to avoid:** Use lifespan handler with `async with` nested context managers
**Warning signs:** "Unclosed client session" warnings in logs

### Pitfall 3: Losing Exceptions in gather(return_exceptions=True)
**What goes wrong:** Errors silently collected but not logged or reported
**Why it happens:** Results contain both values and exceptions mixed together
**How to avoid:** Always iterate results and check `isinstance(result, Exception)`
**Warning signs:** Partial failures not appearing in responses or logs

### Pitfall 4: Creating Clients Per Request
**What goes wrong:** Poor performance, no connection pooling
**Why it happens:** Seems simpler than lifespan management
**How to avoid:** Initialize clients once in lifespan, access via request.state or dependency injection
**Warning signs:** High latency, many TCP connections in netstat

### Pitfall 5: Timeout Not Propagating to Nested Calls
**What goes wrong:** Request-level timeout doesn't affect scraper calls
**Why it happens:** Timeout set on outer client doesn't affect inner operations
**How to avoid:** Pass timeout explicitly to each scraper function or use asyncio.timeout()
**Warning signs:** Requests hanging despite timeout parameter
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns for this integration:

### Sync to Async Client Conversion
```python
# Before (existing sync code)
def create_client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )

# After (async conversion)
def create_async_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers=HEADERS,
        timeout=DEFAULT_TIMEOUT,
    )

# Before
def fetch_event(client: httpx.Client, event_id: str) -> dict:
    response = client.get(f"/api/event/{event_id}")
    response.raise_for_status()
    return response.json()

# After
async def fetch_event(client: httpx.AsyncClient, event_id: str) -> dict:
    response = await client.get(f"/api/event/{event_id}")
    response.raise_for_status()
    return response.json()
```

### Response Model for Scrape Endpoint
```python
from pydantic import BaseModel, Field
from datetime import datetime
from enum import StrEnum

class Platform(StrEnum):
    SPORTYBET = "sportybet"
    BETPAWA = "betpawa"
    BET9JA = "bet9ja"

class PlatformResult(BaseModel):
    platform: Platform
    success: bool
    events_count: int = 0
    error_message: str | None = None
    duration_ms: int

class ScrapeResponse(BaseModel):
    scrape_run_id: int
    status: str  # "completed", "partial", "failed"
    started_at: datetime
    completed_at: datetime
    platforms: list[PlatformResult]
    total_events: int = Field(description="Sum of events across all successful platforms")

    # Optional: full data if requested
    events: list[dict] | None = Field(
        default=None,
        description="Full event data, only included if detail=full"
    )
```

### Health Check Endpoint
```python
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])

class PlatformHealth(BaseModel):
    platform: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: int | None = None
    error: str | None = None

class HealthResponse(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    platforms: list[PlatformHealth]

@router.get("", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    # Check each platform's connectivity
    results = await asyncio.gather(
        check_sportybet(request.state.sportybet_client),
        check_betpawa(request.state.betpawa_client),
        check_bet9ja(request.state.bet9ja_client),
        return_exceptions=True,
    )
    # ... aggregate and return
```
</code_examples>

<existing_code_analysis>
## Existing Scraper Code Analysis

### SportyBet Scraper (scraper/src/sportybet_scraper/)
- **Client:** Sync httpx with tenacity retry
- **Entry point:** `fetch_event(client, event_id)` returns full API response dict
- **Output:** Raw dict with `bizCode`, `data.markets`, team names
- **SportRadar ID:** Passed as input `event_id` parameter

### BetPawa Scraper (scraper/src/betpawa_scraper/)
- **Client:** Sync httpx with tenacity retry
- **Entry points:**
  - `fetch_categories()` → list of CategoryWithRegions
  - `fetch_events(competition_id)` → EventsResponse with EventListItem tuples
  - `fetch_event(event_id)` → full event dict with markets
- **Output:** Dataclass models (EventListItem, Market, Price, etc.)
- **SportRadar ID:** In `widgets` array where `type == "SPORTRADAR"`

### Bet9ja Scraper (scraper/src/bet9ja_scraper/)
- **Client:** Sync httpx with tenacity retry
- **Entry points:**
  - `fetch_sports()` → navigation structure
  - `fetch_events(tournament_id)` → list of EventListItem
  - `fetch_event(event_id)` → EventDetail with flat odds dict
- **Output:** Dataclass models (Sport, EventListItem, EventDetail)
- **SportRadar ID:** `ext_id` field (from `EXTID` in API response)

### Key Integration Findings
1. All three use sync httpx.Client - need async conversion
2. All have tenacity retry decorators - can use same pattern for async
3. BetPawa and Bet9ja have dataclass models, SportyBet returns raw dicts
4. SportRadar ID extraction differs per platform but all support it
5. Existing exception classes (ApiError, NetworkError, InvalidEventIdError) can be reused
</existing_code_analysis>

<open_questions>
## Open Questions

1. **Scraper Package Import Strategy**
   - What we know: Scrapers are in separate package (scraper/) from main app (src/)
   - What's unclear: Should we copy/adapt code or import from scraper package?
   - Recommendation: Create new async clients in src/scraping/ that reuse constants and exception classes from scraper package, but implement async versions of fetch functions

2. **Event Discovery Strategy**
   - What we know: Need to scrape events but don't have event IDs upfront
   - What's unclear: Should we scrape competition listings first or require event IDs?
   - Recommendation: Support both - API can accept specific event IDs or scrape by competition/sport
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Existing scraper code analysis in `scraper/src/` - direct code inspection
- Existing database models in `src/db/models/` - direct code inspection
- [HTTPX Async Documentation](https://www.python-httpx.org/async/) - official async client docs
- [FastAPI Concurrency](https://fastapi.tiangolo.com/async/) - official async guidance

### Secondary (MEDIUM confidence)
- [FastAPI Lifespan Pattern](https://github.com/trondhindenes/fastapi-lifespan-handler) - GitHub example of lifespan with httpx
- [asyncio.gather Exception Handling](https://superfastpython.com/asyncio-gather-exception/) - return_exceptions pattern
- [HTTPX with FastAPI](https://medium.com/@benshearlaw/how-to-use-httpx-request-client-with-fastapi-16255a9984a4) - integration patterns
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) - project structure guidance

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official docs or existing code
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: FastAPI + HTTPX async integration
- Ecosystem: Existing sync scrapers, SQLAlchemy async, Pydantic
- Patterns: Lifespan management, concurrent execution, partial failure handling
- Pitfalls: Event loop blocking, client lifecycle, exception handling

**Confidence breakdown:**
- Standard stack: HIGH - uses existing project dependencies + standard FastAPI
- Architecture: HIGH - patterns from official FastAPI docs and verified examples
- Pitfalls: HIGH - common issues documented in multiple sources
- Code examples: HIGH - adapted from official docs and verified patterns

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - FastAPI/HTTPX ecosystem stable)
</metadata>

---

*Phase: 03-scraper-integration*
*Research completed: 2026-01-20*
*Ready for planning: yes*
