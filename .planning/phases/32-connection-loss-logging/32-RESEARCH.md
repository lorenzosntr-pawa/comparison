# Phase 32: Connection Loss Logging - Research

**Researched:** 2026-01-27
**Domain:** SSE disconnect detection, status management, auto-rescrape recovery
**Confidence:** HIGH

<research_summary>
## Summary

Researched the existing SSE pipeline, progress broadcasting, status model, and scheduler infrastructure to determine how to implement connection loss detection with a new `connection_failed` status and auto-rescrape on recovery.

The codebase already has strong foundations: the backend scrape task runs independently of the SSE connection (`asyncio.create_task` fire-and-forget), the broadcaster handles subscriber disconnection gracefully, and stale detection (Phase 31) already marks hung runs as failed. The key insight is that "connection loss" in this context means the **SSE client disconnects** while the backend scrape task may still be running — so the backend task needs to detect it lost its audience and mark the run accordingly. The frontend side is simpler: detect `EventSource.onerror`, show the `connection_failed` status, and trigger a rescrape.

**Primary recommendation:** Add `CONNECTION_FAILED` to `ScrapeStatus` enum, detect SSE client disconnect in the background scrape task, update run status, and add a `/api/scrape/retry` endpoint that the frontend calls on page reload/reconnection to trigger an immediate rescrape.
</research_summary>

<standard_stack>
## Standard Stack

No new libraries needed. This phase uses existing infrastructure:

### Core (Existing)
| Component | Location | Purpose | Role in Phase 32 |
|-----------|----------|---------|-------------------|
| `ScrapeStatus` enum | `src/db/models/scrape.py:18-25` | Run status values | Add `CONNECTION_FAILED` |
| `ProgressBroadcaster` | `src/scraping/broadcaster.py:14-114` | SSE pub/sub | Detect zero subscribers |
| `ProgressRegistry` | `src/scraping/broadcaster.py:116-183` | Active scrape tracking | Check for orphaned runs |
| `EventSource` (browser) | Frontend hooks | SSE consumption | `onerror` → detect disconnect |
| APScheduler | `src/scheduling/scheduler.py` | Job scheduling | No changes needed |
| structlog | Throughout | Structured logging | Log connection events |

### No New Dependencies Required
This is purely internal infrastructure work using existing patterns.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Current SSE Flow (Manual Scrape)
```
Frontend: new EventSource('/api/scrape/stream')
    ↓
Backend: POST handler creates ScrapeRun + Broadcaster
    ↓
Backend: asyncio.create_task(run_scrape_background()) ← fire-and-forget
    ↓
Background task: orchestrator.scrape_with_progress() yields progress
    ↓
Background task: broadcaster.publish(progress) → subscriber queues
    ↓
SSE endpoint: event_generator() reads from subscriber queue → yields SSE
    ↓
Frontend: eventSource.onmessage → dispatch PROGRESS
```

**Critical architectural fact:** The background scrape task (`run_scrape_background`) is decoupled from the SSE connection. When the client disconnects, the background task keeps running to completion. The SSE generator detects disconnect via `request.is_disconnected()` and breaks out of the loop, but the scrape itself finishes.

### Current SSE Flow (Scheduled Scrape)
```
APScheduler → scrape_all_platforms() job
    ↓
Job creates ScrapeRun + Broadcaster, runs orchestrator
    ↓
Frontend polls /api/scrape/runs/active every 5s
    ↓
Frontend discovers active ID → new EventSource('/api/scrape/runs/{id}/progress')
    ↓
Observation is optional — scrape completes regardless of observers
```

### Pattern 1: Backend Disconnect Detection
**What:** The background scrape task checks if all SSE subscribers disconnected mid-scrape.
**When to use:** Manual scrapes (`trigger="api-stream"`) where the SSE connection was the only way to observe progress.
**Approach:**
- After each platform completes, check `broadcaster.subscriber_count`
- If zero subscribers remain mid-scrape, the client disconnected
- Mark run as `CONNECTION_FAILED` instead of continuing silently
- Log the disconnection event

**Why this works:** The broadcaster already tracks subscribers via its `_subscribers` list. When the SSE generator breaks on `request.is_disconnected()`, it exits the `subscribe()` async generator, which removes the queue from `_subscribers`.

### Pattern 2: Frontend-Driven Rescrape
**What:** When the frontend detects a connection loss or finds a `connection_failed` run, it triggers an immediate rescrape.
**When to use:** Recovery after connection loss.
**Approach:**
- Frontend `EventSource.onerror` fires → mark local state as disconnected
- On page reload or reconnect, check latest run status
- If latest run is `connection_failed`, offer/trigger immediate rescrape
- Use existing `/api/scrape/stream` endpoint (no new endpoint needed)

**Why frontend-driven:** The backend can't know when the frontend "comes back." The frontend knows when it has a working connection again. Simpler than backend-driven heartbeat monitoring of SSE clients.

### Pattern 3: Scheduled Scrape Handling
**What:** Scheduled scrapes don't need connection_failed — they run regardless of observers.
**Key distinction:**
- `trigger="api-stream"` → SSE-initiated, connection loss matters
- `trigger="scheduled"` → Background job, no SSE dependency
- Only manual scrapes should get `CONNECTION_FAILED` status

### Anti-Patterns to Avoid
- **SSE auto-reconnect logic** — Out of scope per CONTEXT.md. The browser's native `EventSource` auto-reconnect is unreliable and adds complexity.
- **Backend SSE heartbeat pinging** — Overengineered for this use case. The `request.is_disconnected()` check already exists.
- **Treating scheduled scrape observation loss as failure** — Scheduled scrapes complete independently. Losing the observation SSE is irrelevant to the scrape's success.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Disconnect detection | Custom ping/pong heartbeat | `request.is_disconnected()` + subscriber count | Already built into Starlette and broadcaster |
| Status badge rendering | New component | Extend existing `StatusBadge` | Existing badge handles all statuses via a map |
| Rescrape trigger | New endpoint | Existing `/api/scrape/stream` | Starting a new scrape IS the retry |
| Connection state tracking | Custom state machine | `EventSource.onerror` + query invalidation | Browser handles SSE lifecycle |

**Key insight:** The existing infrastructure already handles most of this. The broadcaster knows its subscriber count, Starlette knows when a client disconnects, and the frontend already has error handlers on EventSource. The main work is connecting these signals to a new status value and adding logging.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Race Between Scrape Completion and Disconnect Detection
**What goes wrong:** Scrape finishes at the same time client disconnects → run gets marked `CONNECTION_FAILED` instead of `COMPLETED`
**Why it happens:** Background task checks subscribers after final platform, but completion event was already published
**How to avoid:** Only check for disconnect BETWEEN platforms, not after the final one. If all platforms are done, it's COMPLETED regardless of subscriber count.
**Warning signs:** Runs showing `connection_failed` when the scrape actually succeeded

### Pitfall 2: Scheduled Scrapes Getting CONNECTION_FAILED
**What goes wrong:** Scheduled scrapes get `connection_failed` when no frontend is observing
**Why it happens:** Treating all scrapes the same — scheduled scrapes have zero subscribers by default
**How to avoid:** Only apply connection_failed logic to `trigger="api-stream"` runs. Scheduled runs never depend on SSE observers.
**Warning signs:** Scheduled scrapes showing connection_failed when backend is working fine

### Pitfall 3: Stale Detection Conflict
**What goes wrong:** Phase 31's stale detection marks a run as `FAILED` (stale) while Phase 32 logic tries to mark it `CONNECTION_FAILED`
**Why it happens:** Two systems competing to finalize the same run
**How to avoid:** Connection_failed should be set immediately on disconnect detection, before the 10-minute stale threshold. Stale detection should also recognize `CONNECTION_FAILED` as a terminal status (skip those runs).
**Warning signs:** Duplicate status transitions in logs, unexpected status values

### Pitfall 4: Alembic Migration with Enum Change
**What goes wrong:** Adding a new enum value to PostgreSQL enum type requires explicit `ALTER TYPE` in migration
**Why it happens:** SQLAlchemy string-based enums stored as VARCHAR don't need this, but if using native PG enum types, adding values requires migration
**How to avoid:** Check if `ScrapeStatus` is stored as VARCHAR or native PG enum. Current codebase uses `Mapped[str]` with string values — likely VARCHAR, so just adding the Python enum value should work.
**Warning signs:** Migration errors on `ALTER TYPE`
</common_pitfalls>

<code_examples>
## Code Examples

### Current Status Enum (to extend)
```python
# Source: src/db/models/scrape.py:18-25
class ScrapeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    # Phase 32 adds:
    # CONNECTION_FAILED = "connection_failed"
```

### Current Disconnect Check (already exists)
```python
# Source: src/api/routes/scrape.py:256-264
async def event_generator():
    try:
        async for progress in broadcaster.subscribe():
            if await request.is_disconnected():
                break
```

### Current Frontend Error Handler (to enhance)
```typescript
// Source: web/src/features/scrape-runs/hooks/use-scrape-progress.ts:168-174
eventSource.onerror = () => {
  eventSource.close()
  eventSourceRef.current = null
  dispatch({ type: 'DISCONNECTED' })
}
```

### Broadcaster Subscriber Tracking (to leverage)
```python
# Source: src/scraping/broadcaster.py:33-56
async def publish(self, progress: ScrapeProgress) -> None:
    async with self._lock:
        dead_subscribers: list[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                if queue.full():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                queue.put_nowait(progress)
            except Exception:
                dead_subscribers.append(queue)
```

### Background Task Pattern (where disconnect detection goes)
```python
# Source: src/api/routes/scrape.py:176-251
async def run_scrape_background(scrape_run_id: int, broadcaster: ProgressBroadcaster):
    async with async_session_factory() as session:
        # ... scrape logic ...
        async for progress in orchestrator.scrape_with_progress(...):
            await broadcaster.publish(progress)
            # Phase 32: Check subscriber count between platforms here
```

### Stale Detection Terminal Status Check (to update)
```python
# Source: src/scheduling/stale_detection.py:26-73
# Currently finds RUNNING runs — needs to also skip CONNECTION_FAILED
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

No significant changes. SSE is a stable, well-understood technology. The patterns in use (EventSource, Starlette StreamingResponse, pub/sub broadcaster) are current best practices.

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A | N/A | N/A | No ecosystem changes affect this phase |

**Relevant existing infrastructure:**
- Phase 31 (just completed) added stale run detection — CONNECTION_FAILED must integrate with it
- The subscriber tracking in ProgressBroadcaster was built from the start and is reliable
</sota_updates>

<open_questions>
## Open Questions

1. **Should subscriber count be exposed as a property on ProgressBroadcaster?**
   - What we know: `_subscribers` is a private list, currently no public count method
   - What's unclear: Best way to expose — property vs method
   - Recommendation: Add `subscriber_count` property, simple and clean

2. **Should the background task immediately stop scraping on disconnect, or finish current platform?**
   - What we know: User wants the run marked as failed, but partial data may still be useful
   - What's unclear: Whether to abort mid-platform or finish current platform then mark failed
   - Recommendation: Finish current platform, then mark CONNECTION_FAILED. Avoids half-written data.

3. **Frontend rescrape: automatic or manual?**
   - What we know: User wants auto-rescrape on recovery, but "not sure" about backend vs frontend trigger
   - What's unclear: Should it auto-trigger on page load, or show a "Rescrape now" button?
   - Recommendation: Auto-trigger on page load if latest run is connection_failed. Simple, matches user's intent.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Codebase exploration: Full SSE pipeline mapped from backend to frontend
- `src/api/routes/scrape.py` — SSE endpoints, background task pattern
- `src/scraping/broadcaster.py` — ProgressBroadcaster with subscriber tracking
- `src/db/models/scrape.py` — ScrapeStatus enum and ScrapeRun model
- `src/scheduling/stale_detection.py` — Phase 31 watchdog integration point
- `web/src/features/scrape-runs/hooks/use-scrape-progress.ts` — Frontend SSE consumption
- `web/src/features/dashboard/hooks/use-observe-scrape.ts` — Observation hooks
- `web/src/features/dashboard/components/recent-runs.tsx` — Dashboard UI

### Secondary (MEDIUM confidence)
- None needed — this is entirely internal architecture

### Tertiary (LOW confidence)
- None — all findings from direct codebase analysis
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: SSE disconnect detection (Starlette + EventSource)
- Ecosystem: No external libraries needed
- Patterns: Subscriber counting, frontend-driven retry, status enum extension
- Pitfalls: Race conditions, scheduled vs manual distinction, stale detection integration

**Confidence breakdown:**
- Standard stack: HIGH - all existing infrastructure, no new dependencies
- Architecture: HIGH - patterns verified directly in codebase
- Pitfalls: HIGH - identified from code analysis of race conditions and integration points
- Code examples: HIGH - all from actual codebase

**Research date:** 2026-01-27
**Valid until:** 2026-02-27 (internal architecture, stable)
</metadata>

---

*Phase: 32-connection-loss-logging*
*Research completed: 2026-01-27*
*Ready for planning: yes*
