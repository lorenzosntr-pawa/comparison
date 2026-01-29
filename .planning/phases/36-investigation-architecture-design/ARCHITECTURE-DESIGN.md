# Phase 36: Architecture Design Document

**Version:** 1.0
**Created:** 2026-01-29
**Purpose:** Blueprint for v1.7 Scraping Architecture Overhaul (Phases 37-42)

---

## Current State Profiling

### Architecture Overview (Current)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ScrapingOrchestrator                            │
│                                                                     │
│  scrape_with_progress()                                             │
│  ├── _scrape_with_competitor_service() [NEW FLOW]                   │
│  │   ├── Phase 1: BetPawa (sequential)                              │
│  │   │   ├── Competition Discovery (1 API call)                     │
│  │   │   ├── Events List per Competition (N parallel, sem=5)        │
│  │   │   ├── Full Event per Event (M parallel, sem=30)              │
│  │   │   └── DB Storage (sequential)                                │
│  │   └── Phase 2: Competitors (sequential per platform)             │
│  │       ├── SportyBet: fetch-then-store pattern                    │
│  │       │   ├── API Phase (parallel, sem=10 tournaments)           │
│  │       │   ├── DB Phase (sequential)                              │
│  │       │   └── Full Odds Phase (parallel, sem=30)                 │
│  │       └── Bet9ja: fetch-then-store pattern                       │
│  │           ├── API Phase (parallel, sem=10 tournaments)           │
│  │           ├── DB Phase (sequential)                              │
│  │           └── Full Odds Phase (parallel, sem=10 + 50ms delay)    │
│  └── _scrape_legacy_flow() [LEGACY - not used when competitor svc]  │
└─────────────────────────────────────────────────────────────────────┘
```

### Timing Breakdown (Code Review Analysis)

Based on code analysis, the current flow has these timing characteristics:

| Phase | Operation | Concurrency | Estimated Time* |
|-------|-----------|-------------|-----------------|
| **BetPawa** | Competition Discovery | 1 | ~500ms |
| | Events List (per competition) | 5 concurrent | ~2-3s total |
| | Full Event Details | 30 concurrent | ~5-10s total |
| | DB Storage | Sequential | ~2-3s |
| **BetPawa Subtotal** | | | **~10-17s** |
| **SportyBet** | Tournament List (DB read) | 1 | ~100ms |
| | Fetch Events (API) | 10 concurrent | ~3-5s |
| | Store Events (DB) | Sequential | ~2-3s |
| | Full Odds Fetch (API) | 30 concurrent | ~5-8s |
| | Update Snapshots (DB) | Sequential | ~2-3s |
| **SportyBet Subtotal** | | | **~12-19s** |
| **Bet9ja** | Tournament List (DB read) | 1 | ~100ms |
| | Fetch Events (API) | 10 concurrent | ~4-6s |
| | Store Events (DB) | Sequential | ~2-3s |
| | Full Odds Fetch (API) | 10 concurrent + 50ms delay | ~8-12s |
| | Update Snapshots (DB) | Sequential | ~2-3s |
| **Bet9ja Subtotal** | | | **~16-24s** |
| **Total Cycle** | | | **~38-60s** |

*Estimates based on code patterns; actual times vary with network/load.

### Current Semaphore Configuration

```python
# orchestrator.py
BetPawa Competition Semaphore: 5      # Line 965
BetPawa Event Semaphore: 30           # Line 1069

# orchestrator.py (legacy flow)
SportyBet Event Semaphore: 30         # Line 1227
Bet9ja Tournament Semaphore: 10       # Line 1341
Bet9ja Request Delay: 50ms            # Line 1363

# competitor_events.py
SportyBet Tournament Semaphore: 10    # Line 444
Bet9ja Tournament Semaphore: 10       # Line 589
SportyBet Full Odds Semaphore: 30     # Line 737
Bet9ja Full Odds Semaphore: 10        # Line 739
```

### Identified Bottlenecks (Ranked by Impact)

1. **Sequential Platform Execution (CRITICAL)**
   - BetPawa completes fully before competitors start
   - Competitors scrape sequentially (SportyBet then Bet9ja)
   - **Impact:** Odds for same event scraped minutes apart, not simultaneously
   - **Evidence:** Lines 454-586 in orchestrator.py show sequential competitor calls

2. **Per-Event Full Odds Fetch (HIGH)**
   - Each event requires separate API call for full odds
   - SportyBet: 30 concurrent, Bet9ja: 10 concurrent with 50ms delay
   - **Impact:** O(N) API calls where N = total events
   - **Evidence:** Lines 913-957 in competitor_events.py

3. **Sequential DB Storage (MEDIUM)**
   - Events stored one-by-one with individual flush() calls
   - Must wait for flush to get snapshot_id before adding markets
   - **Impact:** DB becomes bottleneck after fast API phase
   - **Evidence:** Lines 513-550 in competitor_events.py

4. **Bet9ja Rate Limiting (LOW-MEDIUM)**
   - Explicit 50ms delay after each tournament fetch
   - Lower concurrency (10 vs 30 for SportyBet)
   - **Impact:** Bet9ja consistently slowest platform
   - **Evidence:** Line 1363 in orchestrator.py

### Key Pattern: Fetch-Then-Store

The codebase established this pattern in v1.1 to avoid SQLAlchemy async session issues:

```
Phase 1 (API): Parallel API calls → collect data in memory
Phase 2 (DB): Sequential DB writes → single session, no concurrency
```

This pattern is **sound** and should be preserved. The new architecture builds on it.

---

## Rate Limit Investigation

### Per-Platform Findings

| Platform | Current Limit | Observed Behavior | Recommended Safe Limit |
|----------|---------------|-------------------|------------------------|
| **BetPawa** | 5 comp + 30 events | No explicit rate limit headers | 5 comp + 50 events |
| **SportyBet** | 30 events | No rate limit headers observed | 50 events |
| **Bet9ja** | 10 tournaments + 50ms | 403 errors seen without delay | 15 tournaments + 25ms |

### BetPawa Rate Limit Analysis

**Client:** `src/scraping/clients/betpawa.py`

- **Headers:** No `X-RateLimit-*` or `Retry-After` headers observed
- **Error handling:** Only 404 triggers InvalidEventIdError
- **Current limits:** Conservative 5 competitions, 30 events
- **Risk assessment:** LOW - Betpawa is primary platform, likely won't throttle own data
- **Recommendation:** Safe to increase event semaphore to 50

```python
# betpawa.py - No rate limit handling needed
# Only network/timeout errors and 404s are handled
```

### SportyBet Rate Limit Analysis

**Client:** `src/scraping/clients/sportybet.py`

- **Headers:** No rate limit headers in response
- **Error handling:** bizCode != 10000 indicates API-level errors
- **Current limits:** 30 events for full odds fetch
- **Risk assessment:** LOW - Uses SportRadar IDs which are standardized
- **Recommendation:** Safe to increase to 50 concurrent

```python
# sportybet.py - Check bizCode for API errors
if data.get("bizCode") != 10000:
    raise InvalidEventIdError(...)
```

### Bet9ja Rate Limit Analysis

**Client:** `src/scraping/clients/bet9ja.py`

- **Headers:** No explicit rate limit headers
- **Error handling:** R != "OK" or R == "E" for errors
- **Current limits:** 10 tournaments with 50ms delay
- **Risk assessment:** MEDIUM - Has shown sensitivity to high request volume
- **Evidence:** The 50ms delay was added in Phase 7.2 after observing issues
- **Recommendation:** Keep delay but reduce to 25ms, increase semaphore to 15

```python
# bet9ja.py - Check "R" result code
if result_code == "E":
    raise InvalidEventIdError(...)
```

### Throttling Detection Patterns

None of the platforms provide explicit rate limit headers. Throttling manifests as:

| Platform | Throttling Signal | Recovery |
|----------|------------------|----------|
| BetPawa | Increased latency, timeouts | Wait + retry |
| SportyBet | bizCode != 10000 | Exponential backoff |
| Bet9ja | R="E" or HTTP 403 | Reduce concurrency + delay |

### Safe Operating Parameters for Parallel Scraping

For the new event-centric architecture:

```python
# Recommended per-platform semaphores for parallel event scraping
SAFE_LIMITS = {
    "betpawa": {
        "concurrent_events": 50,
        "delay_ms": 0,
    },
    "sportybet": {
        "concurrent_events": 50,
        "delay_ms": 0,
    },
    "bet9ja": {
        "concurrent_events": 15,
        "delay_ms": 25,
    },
}
```

---

## EventCoordinator Architecture

### Design Goals

1. **Simultaneous scraping:** For any SR ID, all bookmaker odds are scraped together
2. **Priority-based:** Events starting soon get scraped first
3. **Coverage-aware:** Events with more bookmaker coverage get priority
4. **Observable:** SSE events track per-event progress

### Class Design

```python
# src/scraping/event_coordinator.py (Phase 37 implementation)

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TypedDict
import heapq

class ScrapeStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class EventTarget:
    """Represents a single event to scrape across platforms."""
    sr_id: str
    kickoff: datetime
    platforms: set[str]  # {"betpawa", "sportybet", "bet9ja"}

    # Results after scraping
    status: ScrapeStatus = ScrapeStatus.PENDING
    results: dict[str, dict | None] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def coverage_count(self) -> int:
        return len(self.platforms)

    @property
    def has_betpawa(self) -> bool:
        return "betpawa" in self.platforms

    def priority_key(self) -> tuple:
        """
        Priority ordering (lower = higher priority):
        1. Kickoff time (earlier = higher priority)
        2. Coverage count (more = higher priority, so negate)
        3. Has BetPawa (yes = higher priority, so negate)
        """
        return (
            self.kickoff,
            -self.coverage_count,
            not self.has_betpawa,
        )

class ScrapeBatch(TypedDict):
    """A batch of events to scrape together."""
    batch_id: str
    events: list[EventTarget]
    created_at: datetime

class EventCoordinator:
    """Coordinates event-centric scraping across all bookmakers.

    Flow:
    1. Parallel discovery from all platforms → unified SR ID list
    2. Build priority queue based on kickoff + coverage
    3. Process batches: for each event, scrape all platforms in parallel
    4. Store results with per-event status tracking
    """

    def __init__(
        self,
        betpawa_client: BetPawaClient,
        sportybet_client: SportyBetClient,
        bet9ja_client: Bet9jaClient,
        batch_size: int = 50,
    ) -> None:
        self._clients = {
            "betpawa": betpawa_client,
            "sportybet": sportybet_client,
            "bet9ja": bet9ja_client,
        }
        self._batch_size = batch_size
        self._priority_queue: list[EventTarget] = []
        self._event_map: dict[str, EventTarget] = {}

    async def discover_events(self) -> dict[str, EventTarget]:
        """
        Phase 1: Parallel discovery from all platforms.

        Returns unified event map keyed by SR ID.
        """
        # Run discovery in parallel
        tasks = [
            self._discover_betpawa(),
            self._discover_sportybet(),
            self._discover_bet9ja(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge into unified event map
        for platform, events in zip(["betpawa", "sportybet", "bet9ja"], results):
            if isinstance(events, Exception):
                continue
            for event in events:
                sr_id = event["sr_id"]
                if sr_id in self._event_map:
                    self._event_map[sr_id].platforms.add(platform)
                else:
                    self._event_map[sr_id] = EventTarget(
                        sr_id=sr_id,
                        kickoff=event["kickoff"],
                        platforms={platform},
                    )

        return self._event_map

    def build_priority_queue(self) -> list[EventTarget]:
        """
        Phase 2: Build priority queue from discovered events.

        Priority: kickoff ASC, coverage DESC, has_betpawa DESC
        """
        self._priority_queue = list(self._event_map.values())
        heapq.heapify(
            self._priority_queue,
            key=lambda e: e.priority_key(),
        )
        return self._priority_queue

    def get_next_batch(self) -> ScrapeBatch | None:
        """
        Get next batch of events to scrape.

        Returns batch_size events from priority queue.
        """
        if not self._priority_queue:
            return None

        batch_events = []
        for _ in range(min(self._batch_size, len(self._priority_queue))):
            event = heapq.heappop(self._priority_queue)
            batch_events.append(event)

        return ScrapeBatch(
            batch_id=f"batch_{datetime.now().timestamp()}",
            events=batch_events,
            created_at=datetime.now(),
        )

    async def scrape_batch(
        self,
        batch: ScrapeBatch,
    ) -> AsyncGenerator[ScrapeProgress, None]:
        """
        Phase 3: Scrape all events in batch.

        For each event, scrapes all available platforms in parallel.
        Yields progress updates for SSE streaming.
        """
        for event in batch.events:
            event.status = ScrapeStatus.IN_PROGRESS

            # Emit EVENT_SCRAPING progress
            yield ScrapeProgress(
                event_type="EVENT_SCRAPING",
                sr_id=event.sr_id,
                platforms_pending=list(event.platforms),
            )

            # Scrape all platforms in parallel
            results = await self._scrape_event_all_platforms(event)

            # Update event with results
            event.results = results["data"]
            event.errors = results["errors"]
            event.status = (
                ScrapeStatus.COMPLETED
                if not event.errors
                else ScrapeStatus.FAILED
            )

            # Emit EVENT_SCRAPED progress
            yield ScrapeProgress(
                event_type="EVENT_SCRAPED",
                sr_id=event.sr_id,
                platforms_scraped=list(event.results.keys()),
                platforms_failed=list(event.errors.keys()),
                timing_ms=results["timing_ms"],
            )

    async def _scrape_event_all_platforms(
        self,
        event: EventTarget,
    ) -> dict:
        """Scrape single event from all available platforms in parallel."""
        platform_semaphores = {
            "betpawa": asyncio.Semaphore(50),
            "sportybet": asyncio.Semaphore(50),
            "bet9ja": asyncio.Semaphore(15),
        }

        async def scrape_platform(platform: str) -> tuple[str, dict | None, str | None]:
            async with platform_semaphores[platform]:
                try:
                    client = self._clients[platform]
                    data = await client.fetch_event(
                        self._format_event_id(event.sr_id, platform)
                    )
                    if platform == "bet9ja":
                        await asyncio.sleep(0.025)  # 25ms delay
                    return (platform, data, None)
                except Exception as e:
                    return (platform, None, str(e))

        start = time.perf_counter()
        tasks = [scrape_platform(p) for p in event.platforms]
        results = await asyncio.gather(*tasks)
        timing_ms = int((time.perf_counter() - start) * 1000)

        return {
            "data": {p: d for p, d, e in results if d is not None},
            "errors": {p: e for p, d, e in results if e is not None},
            "timing_ms": timing_ms,
        }

    @staticmethod
    def _format_event_id(sr_id: str, platform: str) -> str:
        """Format SR ID for platform-specific API."""
        if platform == "sportybet":
            return f"sr:match:{sr_id}"
        return sr_id  # BetPawa and Bet9ja use SR ID directly
```

### Interface Summary

```python
class EventCoordinator:
    # Discovery
    async def discover_events() -> dict[str, EventTarget]

    # Queue management
    def build_priority_queue() -> list[EventTarget]
    def get_next_batch() -> ScrapeBatch | None

    # Scraping
    async def scrape_batch(batch) -> AsyncGenerator[ScrapeProgress, None]

    # Helpers
    async def _discover_betpawa() -> list[dict]
    async def _discover_sportybet() -> list[dict]
    async def _discover_bet9ja() -> list[dict]
    async def _scrape_event_all_platforms(event) -> dict
```

---

## Priority Queue Design

### Ordering Algorithm

Events are prioritized using a composite key:

```
priority = (kickoff_time, -coverage_count, not has_betpawa)
```

**Interpretation:**
1. **kickoff_time ASC:** Events starting soon are most urgent
2. **coverage_count DESC:** Events with 3 bookmakers > 2 > 1
3. **has_betpawa:** BetPawa presence adds value (primary platform)

### Priority Tiers

| Tier | Kickoff Window | Coverage | Description |
|------|----------------|----------|-------------|
| 1 | < 30 minutes | 3 platforms | Urgent, full comparison value |
| 2 | < 30 minutes | 2+ with BetPawa | Urgent, some comparison value |
| 3 | < 30 minutes | Any | Urgent, capture what's available |
| 4 | 30min - 2hr | 3 platforms | Soon, full comparison |
| 5 | 30min - 2hr | 2+ with BetPawa | Soon, some comparison |
| 6 | > 2hr | Any | Future, lowest priority |

### Implementation

```python
def priority_key(event: EventTarget) -> tuple:
    """
    Returns tuple for min-heap ordering.
    Lower values = higher priority.
    """
    # Tier by kickoff urgency
    now = datetime.now(timezone.utc)
    minutes_until = (event.kickoff - now).total_seconds() / 60

    if minutes_until < 30:
        urgency = 0
    elif minutes_until < 120:
        urgency = 1
    else:
        urgency = 2

    # Coverage score (negate for max-first)
    coverage = -event.coverage_count

    # BetPawa presence (negate for presence = higher priority)
    has_bp = 0 if event.has_betpawa else 1

    return (urgency, event.kickoff, coverage, has_bp)
```

---

## Per-Event Parallel Scraping

### Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    scrape_batch(batch)                           │
├──────────────────────────────────────────────────────────────────┤
│  for event in batch.events:                                      │
│      ┌──────────────────────────────────────────────────────┐    │
│      │ _scrape_event_all_platforms(event)                   │    │
│      │                                                      │    │
│      │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │    │
│      │   │   BetPawa   │  │  SportyBet  │  │   Bet9ja    │ │    │
│      │   │ (sem=50)    │  │  (sem=50)   │  │ (sem=15)    │ │    │
│      │   │             │  │             │  │  +25ms      │ │    │
│      │   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │    │
│      │          │                │                │        │    │
│      │          ▼                ▼                ▼        │    │
│      │   ┌─────────────────────────────────────────────┐   │    │
│      │   │           asyncio.gather()                  │   │    │
│      │   │    (all 3 platforms for this event)         │   │    │
│      │   └─────────────────────────────────────────────┘   │    │
│      │                          │                          │    │
│      │                          ▼                          │    │
│      │   ┌─────────────────────────────────────────────┐   │    │
│      │   │         event.results = {...}               │   │    │
│      │   │         yield ScrapeProgress(...)           │   │    │
│      │   └─────────────────────────────────────────────┘   │    │
│      └──────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│      ┌──────────────────────────────────────────────────────┐    │
│      │           Next event in batch...                     │    │
│      └──────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

### Pseudocode

```python
async def scrape_cycle():
    """Complete scrape cycle using EventCoordinator."""
    coordinator = EventCoordinator(clients)

    # Phase 1: Parallel discovery
    await coordinator.discover_events()

    # Phase 2: Build priority queue
    coordinator.build_priority_queue()

    # Phase 3: Process batches
    while batch := coordinator.get_next_batch():
        # Phase 4: Scrape batch with SSE progress
        async for progress in coordinator.scrape_batch(batch):
            yield progress

        # Phase 5: Store batch results
        await store_batch_results(batch)
```

### Concurrency Model

```
Global level:     1 batch at a time (sequential)
Batch level:      1 event at a time (sequential for ordering)
Event level:      3 platforms in parallel (simultaneous)
Platform level:   Semaphore-controlled (50/50/15)
```

This ensures:
- Events are processed in priority order
- Odds for each event are captured simultaneously
- Rate limits are respected per-platform

---

## Observability Design

### SSE Event Types

| Event Type | Payload | When Emitted |
|------------|---------|--------------|
| `CYCLE_START` | `{total_events, batch_count}` | Start of scrape cycle |
| `DISCOVERY_COMPLETE` | `{betpawa: N, sportybet: N, bet9ja: N, merged: N}` | After parallel discovery |
| `BATCH_START` | `{batch_id, event_count, batch_index}` | Start of each batch |
| `EVENT_SCRAPING` | `{sr_id, platforms_pending}` | Before scraping event |
| `EVENT_SCRAPED` | `{sr_id, platforms_scraped, platforms_failed, timing_ms}` | After scraping event |
| `BATCH_COMPLETE` | `{batch_id, events_scraped, events_failed, timing_ms}` | End of batch |
| `CYCLE_COMPLETE` | `{total_events, total_timing_ms, success_rate}` | End of cycle |

### Progress Schema

```python
@dataclass
class ScrapeProgress:
    """SSE progress event for event-centric scraping."""
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Cycle-level
    scrape_run_id: int | None = None
    total_events: int | None = None
    batch_count: int | None = None

    # Batch-level
    batch_id: str | None = None
    batch_index: int | None = None

    # Event-level
    sr_id: str | None = None
    platforms_pending: list[str] | None = None
    platforms_scraped: list[str] | None = None
    platforms_failed: list[str] | None = None
    timing_ms: int | None = None

    # Discovery counts
    discovery_counts: dict[str, int] | None = None

    # Error info
    error: str | None = None
```

### Frontend Integration

The UI can track:
1. **Overall progress:** `events_scraped / total_events` progress bar
2. **Per-event status:** Show which events are in-progress
3. **Platform health:** Track which platforms are failing
4. **Timing:** Show scrape duration and ETA

```typescript
// SSE event handling in React
interface EventProgress {
  sr_id: string;
  status: 'pending' | 'scraping' | 'completed' | 'failed';
  platforms: {
    betpawa: 'pending' | 'scraped' | 'failed';
    sportybet: 'pending' | 'scraped' | 'failed';
    bet9ja: 'pending' | 'scraped' | 'failed';
  };
  timing_ms?: number;
}
```

---

## Phase Mapping

### Design Sections to Implementation Phases

| Design Section | Phase | Implementation Focus |
|----------------|-------|---------------------|
| EventCoordinator class | **Phase 37** | Core class, discovery methods, event map |
| Priority Queue | **Phase 37** | Queue building, batch extraction |
| Per-Event Parallel Scraping | **Phase 38** | `scrape_batch()`, `_scrape_event_all_platforms()` |
| Platform Semaphores | **Phase 38** | Concurrency control per platform |
| Batch DB Storage | **Phase 39** | `store_batch_results()`, bulk inserts |
| Per-Event Status Table | **Phase 39** | New DB model for tracking scrape status |
| Semaphore Tuning | **Phase 40** | Adjust limits based on production metrics |
| Performance Metrics | **Phase 40** | Timing histograms, success rates |
| SSE Observability | **Phase 40** | Implement new event types |
| On-Demand API | **Phase 41** | `POST /api/scrape/{sr_id}` endpoint |
| Legacy Flow Removal | **Phase 42** | Remove old orchestrator paths |

### Phase Dependencies

```
Phase 36 (this) ──────────────────────────────────────────┐
                                                          │
Phase 37: EventCoordinator ◄──────────────────────────────┘
    │
    ├── EventTarget dataclass
    ├── EventCoordinator class
    ├── discover_events() methods
    └── build_priority_queue()
    │
    ▼
Phase 38: SR ID Parallel Scraping
    │
    ├── scrape_batch() implementation
    ├── _scrape_event_all_platforms()
    └── Per-platform semaphores
    │
    ▼
Phase 39: Batch DB Storage
    │
    ├── store_batch_results()
    ├── Bulk insert patterns
    └── Per-event status model
    │
    ▼
Phase 40: Concurrency Tuning
    │
    ├── Optimize semaphore limits
    ├── Add performance metrics
    └── SSE event implementation
    │
    ▼
Phase 41: On-Demand API
    │
    ├── POST /api/scrape/{sr_id}
    └── Single-event refresh
    │
    ▼
Phase 42: Validation & Cleanup
    │
    ├── Side-by-side testing
    └── Remove legacy flow
```

---

## Appendix: Key Files Reference

### Current Implementation
- `src/scraping/orchestrator.py` - Current orchestrator with competitor service
- `src/scraping/competitor_events.py` - Fetch-then-store pattern reference
- `src/scraping/clients/betpawa.py` - BetPawa API client
- `src/scraping/clients/sportybet.py` - SportyBet API client
- `src/scraping/clients/bet9ja.py` - Bet9ja API client

### New Files (Phase 37+)
- `src/scraping/event_coordinator.py` - EventCoordinator implementation
- `src/scraping/schemas/coordinator.py` - EventTarget, ScrapeBatch types
- `src/db/models/scrape_status.py` - Per-event status tracking

---

*Document created: 2026-01-29*
*Phase: 36-investigation-architecture-design*
