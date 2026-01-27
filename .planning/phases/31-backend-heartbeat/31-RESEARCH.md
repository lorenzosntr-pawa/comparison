# Phase 31: Backend Heartbeat & Stale Run Detection - Research

**Researched:** 2026-01-27
**Domain:** asyncio background task monitoring, stale process detection
**Confidence:** HIGH

<research_summary>
## Summary

Researched the existing scraping infrastructure to determine how to add heartbeat monitoring for stale RUNNING scrape runs. The codebase already has all necessary primitives: ScrapeRun model with status tracking, ScrapePhaseLog with timestamps for audit trail, APScheduler for periodic jobs, and ProgressBroadcaster for real-time updates.

The standard approach is a periodic watchdog job (via APScheduler) that queries for RUNNING scrape runs whose last activity exceeds a configurable staleness threshold. No new tables or models are needed — `ScrapePhaseLog.entered_at` already provides the "last activity" timestamp, and `ScrapeRun.started_at` provides a fallback.

**Primary recommendation:** Add an APScheduler job that runs every 2 minutes, queries for RUNNING scrapes with no phase log activity for 10+ minutes, and marks them FAILED with error_type="stale" and a descriptive message including last known phase/platform.
</research_summary>

<standard_stack>
## Standard Stack

No new libraries needed. Everything required already exists in the codebase:

### Existing Infrastructure (Already Available)
| Component | Location | Purpose | How It Helps |
|-----------|----------|---------|--------------|
| ScrapeRun model | src/db/models/scrape.py | Run tracking with status field | Query RUNNING runs, update to FAILED |
| ScrapePhaseLog model | src/db/models/scrape.py | Phase transition timestamps | Detect last activity time |
| ScrapeError model | src/db/models/scrape.py | Error records | Log stale detection as error |
| ScrapeStatus enum | src/db/models/scrape.py | PENDING/RUNNING/COMPLETED/PARTIAL/FAILED | Status transitions |
| APScheduler | src/scheduling/scheduler.py | Periodic job execution | Run watchdog on interval |
| ProgressBroadcaster | src/scraping/broadcaster.py | SSE pub/sub | Close stale broadcasters |
| ProgressRegistry | src/scraping/broadcaster.py | Active scrape tracking | Find active broadcasters to clean up |
| async_session_factory | src/db/session.py | DB session creation | Independent session for watchdog |
| structlog | Throughout | Structured logging | Log stale detections |

### No New Dependencies Required
This is purely internal infrastructure using existing patterns.
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: APScheduler Watchdog Job
**What:** A lightweight periodic job added to the existing scheduler that checks for stale runs.
**When to use:** This is the only pattern needed.
**How it works:**
```python
# In scheduler.py - add alongside existing jobs
scheduler.add_job(
    detect_stale_runs,
    trigger=IntervalTrigger(minutes=2),
    id="detect_stale_runs",
    name="Detect stale scrape runs",
    misfire_grace_time=60,
    coalesce=True,
)
```

### Pattern 2: Last Activity Detection via ScrapePhaseLog
**What:** Use the existing `ScrapePhaseLog.entered_at` timestamp to determine when a run last showed signs of life.
**Why this works:** Every phase transition already creates a ScrapePhaseLog record with a timestamp. If no new records appear for N minutes, the run is stale.
**Fallback:** If no ScrapePhaseLog exists (run died before first phase), use `ScrapeRun.started_at`.

```python
# Query pattern:
# 1. Find RUNNING scrape runs
# 2. For each, find MAX(scrape_phase_logs.entered_at)
# 3. If (now - last_activity) > threshold → stale
```

### Pattern 3: Clean Failure with Context
**What:** When marking a run as FAILED, include rich context about what was happening when it went stale.
**Fields to populate:**
- `ScrapeRun.status` → "failed"
- `ScrapeRun.completed_at` → now
- `ScrapeError` record with error_type="stale", message including last phase/platform/timing
- Close associated ProgressBroadcaster if still active

### Anti-Patterns to Avoid
- **Heartbeat column on ScrapeRun:** Don't add a `last_heartbeat` column that gets updated every N seconds. The existing ScrapePhaseLog already provides activity timestamps. Adding a heartbeat column means modifying the orchestrator hot path — unnecessary coupling.
- **Separate heartbeat table:** Overkill. ScrapePhaseLog already serves as an activity log.
- **In-memory-only tracking:** Must be DB-based so it survives process restarts.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Periodic execution | Custom asyncio loop with sleep | APScheduler IntervalTrigger | Already configured, handles misfires, coalescing |
| Activity timestamps | New heartbeat model/table | Existing ScrapePhaseLog.entered_at | Already tracks every phase transition with timing |
| Error recording | Custom error logging | Existing ScrapeError model | Already has error_type, error_message, platform fields |
| Broadcaster cleanup | Manual socket/queue teardown | ProgressRegistry.remove_broadcaster() | Already handles subscriber cleanup |

**Key insight:** The codebase already has every building block. Phase 31 is primarily a new job function + a query, not new infrastructure.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Race Condition with Active Scrapes
**What goes wrong:** Watchdog marks a run as FAILED while the orchestrator is still actively working on it (just slow, not dead).
**Why it happens:** Staleness threshold too aggressive, or not checking latest activity.
**How to avoid:** Use 10-minute threshold (2x the default scrape interval of 5 min). Check ScrapePhaseLog for most recent activity, not just ScrapeRun.started_at.
**Warning signs:** Runs marked stale that were actually completing normally.

### Pitfall 2: Concurrent DB Session Conflicts
**What goes wrong:** Watchdog updates ScrapeRun status while orchestrator is also updating it, causing stale data overwrites.
**Why it happens:** AsyncSession cannot be shared across concurrent tasks (documented pattern from v1.0).
**How to avoid:** Watchdog creates its own session. Use SELECT FOR UPDATE or optimistic check: only update if status is still RUNNING at commit time.
**Warning signs:** Completed runs showing as FAILED, or status flickering.

### Pitfall 3: Orphaned Broadcasters
**What goes wrong:** Watchdog marks run as FAILED but doesn't clean up the ProgressBroadcaster, leaving SSE subscribers hanging.
**Why it happens:** Forgetting to close broadcaster when externally failing a run.
**How to avoid:** After marking FAILED, explicitly call `progress_registry.remove_broadcaster(scrape_run_id)` and `broadcaster.close()`.
**Warning signs:** SSE connections that never terminate, memory leaks from accumulated queues.

### Pitfall 4: Startup Recovery Gap
**What goes wrong:** Server crashes with RUNNING scrapes, restarts, but watchdog hasn't run yet — stale runs linger until first check.
**Why it happens:** APScheduler job only runs on interval, not immediately at startup.
**How to avoid:** Run stale detection once at startup (during app lifespan). Catch any RUNNING runs from before the restart.
**Warning signs:** Stale runs surviving server restarts for the full check interval.
</common_pitfalls>

<code_examples>
## Code Examples

### Stale Run Query Pattern
```python
# Source: Codebase analysis of existing models
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone

async def find_stale_runs(db: AsyncSession, stale_threshold_minutes: int = 10):
    """Find RUNNING scrape runs with no recent activity."""
    threshold = datetime.now(timezone.utc) - timedelta(minutes=stale_threshold_minutes)

    # Subquery: latest phase log per scrape run
    latest_activity = (
        select(
            ScrapePhaseLog.scrape_run_id,
            func.max(ScrapePhaseLog.entered_at).label("last_activity")
        )
        .group_by(ScrapePhaseLog.scrape_run_id)
        .subquery()
    )

    # Find RUNNING runs where last activity is before threshold
    stmt = (
        select(ScrapeRun)
        .outerjoin(latest_activity, ScrapeRun.id == latest_activity.c.scrape_run_id)
        .where(ScrapeRun.status == ScrapeStatus.RUNNING)
        .where(
            # Either: last phase log is stale, OR no phase logs and started_at is stale
            (latest_activity.c.last_activity < threshold) |
            (latest_activity.c.last_activity.is_(None) & (ScrapeRun.started_at < threshold))
        )
    )

    result = await db.execute(stmt)
    return result.scalars().all()
```

### Mark Run as Stale-Failed
```python
async def mark_run_stale(db: AsyncSession, run: ScrapeRun, last_activity: datetime | None):
    """Mark a stale RUNNING run as FAILED with context."""
    now = datetime.now(timezone.utc)
    stale_duration = now - (last_activity or run.started_at)

    run.status = ScrapeStatus.FAILED
    run.completed_at = now

    # Create descriptive error
    error = ScrapeError(
        scrape_run_id=run.id,
        error_type="stale",
        error_message=(
            f"Run marked stale: no progress for {stale_duration.total_seconds() / 60:.0f} minutes. "
            f"Last phase: {run.current_phase or 'unknown'}, "
            f"last platform: {run.current_platform or 'unknown'}"
        ),
        occurred_at=now,
    )
    db.add(error)
    await db.commit()
```

### Startup Recovery
```python
# In app lifespan (src/api/app.py)
async def recover_stale_runs():
    """On startup, fail any RUNNING runs from previous process."""
    async with async_session_factory() as db:
        stmt = select(ScrapeRun).where(ScrapeRun.status == ScrapeStatus.RUNNING)
        result = await db.execute(stmt)
        stale_runs = result.scalars().all()

        for run in stale_runs:
            await mark_run_stale(db, run, last_activity=None)
            log.info("Recovered stale run from previous process", scrape_run_id=run.id)
```
</code_examples>

<sota_updates>
## State of the Art

No SOTA concerns — this is standard asyncio/SQLAlchemy background task monitoring. The patterns used are well-established and stable.

The existing APScheduler + SQLAlchemy async stack is the right tool for this job.
</sota_updates>

<open_questions>
## Open Questions

1. **Staleness threshold value**
   - What we know: Default scrape interval is 5 minutes, per-platform timeout is 300s (5 min)
   - Recommendation: 10 minutes (2x scrape interval) is safe default. Configurable via settings table.

2. **Check interval for watchdog**
   - What we know: Need to balance responsiveness vs DB load
   - Recommendation: Every 2 minutes. Cheap query, quick detection.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Codebase analysis: src/db/models/scrape.py (ScrapeRun, ScrapePhaseLog, ScrapeError models)
- Codebase analysis: src/scraping/orchestrator.py (scrape lifecycle, phase transitions)
- Codebase analysis: src/scraping/broadcaster.py (ProgressBroadcaster, ProgressRegistry)
- Codebase analysis: src/scheduling/scheduler.py (APScheduler configuration)
- Codebase analysis: src/scheduling/jobs.py (scheduled scrape job pattern)
- Codebase analysis: src/api/routes/scrape.py (SSE streaming, background task pattern)
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: asyncio background tasks, SQLAlchemy async queries
- Ecosystem: APScheduler (already in use), existing models
- Patterns: Watchdog job, stale detection query, startup recovery
- Pitfalls: Race conditions, orphaned broadcasters, session conflicts

**Confidence breakdown:**
- Standard stack: HIGH - all components already exist in codebase
- Architecture: HIGH - follows established codebase patterns exactly
- Pitfalls: HIGH - derived from documented codebase constraints (AsyncSession sharing)
- Code examples: HIGH - based on actual model schemas and query patterns

**Research date:** 2026-01-27
**Valid until:** Indefinite (internal patterns, no external dependencies)
</metadata>

---

*Phase: 31-backend-heartbeat*
*Research completed: 2026-01-27*
*Ready for planning: yes*
