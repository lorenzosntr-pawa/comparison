# Phase 5: Scheduled Scraping - Research

**Researched:** 2026-01-20
**Domain:** Background task scheduling for async FastAPI application
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Python ecosystem for background job scheduling in async FastAPI applications. The user wants simple interval-based scraping with active monitoring (platform health + run history), reliability, and visibility — no external alerting.

For this use case, **APScheduler 3.x with AsyncIOScheduler** is the right choice. It's mature, well-documented, and integrates cleanly with FastAPI's lifespan context manager. ARQ requires Redis (overkill for simple intervals), Celery is heavy, and native asyncio lacks job persistence and monitoring features.

Key finding: APScheduler runs jobs in-process, which is exactly what we need for a single-instance FastAPI app. For multi-worker deployments (Gunicorn with multiple workers), APScheduler would need to run in a separate dedicated process — but with Uvicorn single-worker, it integrates directly into the FastAPI lifespan.

**Primary recommendation:** Use APScheduler 3.x AsyncIOScheduler integrated via FastAPI lifespan, with in-memory job store (schedules are defined in code, not dynamically created), plus custom run history tracking in PostgreSQL for monitoring visibility.

</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 3.10.x | Job scheduling | Mature, async-native with AsyncIOScheduler, well-documented |
| tenacity | 8.x | Retry logic | Standard for retry with exponential backoff, supports async |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (built-in) asyncio | stdlib | Event loop | Already using for FastAPI |
| (existing) SQLAlchemy | 2.x | Run history persistence | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler | ARQ | ARQ requires Redis, better for distributed task queues, overkill for simple intervals |
| APScheduler | Celery | Celery is heavyweight, requires message broker, better for complex distributed workflows |
| APScheduler | Native asyncio.create_task | No persistence, no job management, no monitoring hooks |
| APScheduler | APScheduler 4.x | 4.x is still alpha (4.0.0a6), not production-ready, API not stable |

**Installation:**
```bash
pip install apscheduler tenacity
```

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── scheduling/
│   ├── __init__.py
│   ├── scheduler.py      # AsyncIOScheduler setup and job definitions
│   ├── jobs.py           # Actual job functions (scrape_all, etc.)
│   └── history.py        # Run history models and tracking
├── api/
│   └── routes/
│       └── scheduler.py  # Monitoring endpoints (status, history)
```

### Pattern 1: Lifespan Integration
**What:** Start/stop scheduler in FastAPI lifespan context manager
**When to use:** Always for APScheduler + FastAPI
**Example:**
```python
# Source: APScheduler docs + FastAPI lifespan docs
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: Job Definition with replace_existing
**What:** Define jobs at startup with explicit IDs and replace_existing=True
**When to use:** For code-defined schedules (not dynamic)
**Example:**
```python
# Source: APScheduler user guide
from apscheduler.triggers.interval import IntervalTrigger

def setup_jobs():
    scheduler.add_job(
        scrape_all_platforms,
        trigger=IntervalTrigger(minutes=5),
        id="scrape_all",
        replace_existing=True,  # Prevents duplicate on restart
        misfire_grace_time=60,  # Allow 60s late execution
        coalesce=True,          # Combine missed runs into one
    )
```

### Pattern 3: Run History Tracking
**What:** Log each job run to database for monitoring visibility
**When to use:** When user wants to see run history (active monitoring)
**Example:**
```python
# Custom pattern for visibility
from datetime import datetime
from sqlalchemy import insert

async def scrape_all_platforms():
    run_id = await log_run_start("scrape_all")
    try:
        results = await orchestrator.scrape_all()
        await log_run_complete(run_id, status="success", results=results)
    except Exception as e:
        await log_run_complete(run_id, status="failed", error=str(e))
        raise  # Re-raise for APScheduler error handling
```

### Pattern 4: Graceful Error Handling
**What:** Jobs should catch errors, log them, and not crash the scheduler
**When to use:** Always for production jobs
**Example:**
```python
# Source: Best practices from APScheduler + tenacity docs
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
async def scrape_platform(platform: Platform):
    """Scrape with retry logic per platform."""
    client = get_client(platform)
    return await client.fetch_events()

async def scrape_all_platforms():
    """Main job - handles partial failures gracefully."""
    results = await asyncio.gather(
        scrape_platform(Platform.BETPAWA),
        scrape_platform(Platform.SPORTYBET),
        scrape_platform(Platform.BET9JA),
        return_exceptions=True
    )
    # Log results, some may be exceptions
    for platform, result in zip(Platform, results):
        if isinstance(result, Exception):
            logger.error(f"{platform} failed: {result}")
        else:
            logger.info(f"{platform} succeeded: {len(result)} events")
```

### Anti-Patterns to Avoid
- **Blocking the event loop:** Never use sync sleep or blocking I/O in async jobs
- **No error handling:** Unhandled exceptions in jobs can cause scheduler issues
- **Dynamic job stores with multiple workers:** APScheduler job stores don't synchronize across processes
- **Ignoring misfire_grace_time:** Without it, delayed jobs may not run at all

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Interval scheduling | Custom asyncio.sleep loop | APScheduler IntervalTrigger | Handles edge cases: missed runs, shutdown, timezone |
| Retry with backoff | Custom retry logic | tenacity decorator | Battle-tested, handles jitter, async support |
| Job coalescing | Custom "last run" tracking | APScheduler coalesce=True | Built-in, handles edge cases correctly |
| Graceful shutdown | Signal handlers | APScheduler shutdown(wait=True) | Waits for running jobs to complete |

**Key insight:** Simple interval scheduling looks trivial but has many edge cases: What if a job is still running when the next interval fires? What if the app restarts mid-job? What if system time changes? APScheduler handles all of these; a naive asyncio.sleep loop does not.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Multiple Scheduler Instances with Multi-Worker
**What goes wrong:** Jobs run N times per interval (once per worker)
**Why it happens:** Gunicorn/Uvicorn with multiple workers each start their own scheduler
**How to avoid:** Use single-worker Uvicorn, OR run scheduler in separate process
**Warning signs:** Same job runs 2-4x simultaneously, duplicate database entries

### Pitfall 2: Jobs Block Event Loop
**What goes wrong:** API requests timeout, scheduler appears stuck
**Why it happens:** Sync code (requests, time.sleep) in async jobs
**How to avoid:** Use async clients (httpx.AsyncClient), asyncio.sleep()
**Warning signs:** All requests slow during job execution

### Pitfall 3: Memory Leak from Unfinished Jobs
**What goes wrong:** Memory grows over time, eventually OOM
**Why it happens:** Jobs create resources (connections, sessions) but don't clean up on error
**How to avoid:** Use context managers (async with), ensure cleanup in finally blocks
**Warning signs:** Memory usage increases after each job run

### Pitfall 4: Missed Jobs After Restart
**What goes wrong:** Job doesn't run for a long time after restart
**Why it happens:** Default misfire_grace_time is 1 second, job "missed" if startup slow
**How to avoid:** Set reasonable misfire_grace_time (e.g., 60 seconds)
**Warning signs:** Jobs skip runs after deployments

### Pitfall 5: No Visibility into Job Status
**What goes wrong:** User can't tell if scraping is working
**Why it happens:** APScheduler doesn't persist run history by default
**How to avoid:** Add custom run history logging to database
**Warning signs:** "Is it even running?" questions from users

</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### AsyncIOScheduler Setup with FastAPI
```python
# Source: APScheduler docs + FastAPI lifespan docs
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

scheduler = AsyncIOScheduler(timezone="UTC")

async def scrape_job():
    """The actual scraping job."""
    # Implementation here
    pass

def configure_scheduler():
    """Add all scheduled jobs."""
    scheduler.add_job(
        scrape_job,
        trigger=IntervalTrigger(minutes=5),
        id="scrape_all_platforms",
        replace_existing=True,
        misfire_grace_time=60,
        coalesce=True,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)
```

### Retry with Tenacity (Async)
```python
# Source: tenacity docs
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    reraise=True,
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str):
    response = await client.get(url, timeout=30.0)
    response.raise_for_status()
    return response.json()
```

### Scheduler Status Endpoint
```python
# Pattern for monitoring visibility
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

class JobStatus(BaseModel):
    id: str
    next_run: datetime | None
    last_run: datetime | None

class SchedulerStatus(BaseModel):
    running: bool
    jobs: list[JobStatus]

@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(JobStatus(
            id=job.id,
            next_run=job.next_run_time,
            last_run=None,  # Would come from run history table
        ))
    return SchedulerStatus(
        running=scheduler.running,
        jobs=jobs,
    )
```

</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| APScheduler 3.x | APScheduler 4.x (alpha) | 2024-2025 | 4.x has better multi-node support but is NOT stable yet |
| pytz timezones | zoneinfo (stdlib) | Python 3.9+ | Use zoneinfo, pytz deprecated in APScheduler |
| @app.on_event("startup") | lifespan context manager | FastAPI 0.95+ | Lifespan is the recommended approach |
| Celery for everything | APScheduler for simple, ARQ/Celery for distributed | 2023+ | Right-size the tool to the problem |

**New tools/patterns to consider:**
- **APScheduler 4.x (when stable):** Will have better multi-node support with event brokers
- **ARQ:** Good middle ground between APScheduler and Celery if Redis is already in stack

**Deprecated/outdated:**
- **@app.on_event("startup"):** Still works but lifespan is preferred
- **pytz:** Use zoneinfo instead
- **APScheduler job stores for multi-worker sync:** Doesn't work, use separate process

</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Interval configuration source**
   - What we know: User wants simple intervals, one global setting
   - What's unclear: Should interval be env var, config file, or hardcoded?
   - Recommendation: Use environment variable (SCRAPE_INTERVAL_MINUTES) with sensible default (5)

2. **Run history retention**
   - What we know: User wants to see run history
   - What's unclear: How long to keep history? Days? Weeks?
   - Recommendation: Keep 7 days by default, add cleanup job

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [APScheduler 3.x User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) - scheduler types, triggers, job stores, configuration
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - lifespan context manager pattern
- [tenacity PyPI](https://pypi.org/project/tenacity/) - retry decorator usage

### Secondary (MEDIUM confidence)
- [APScheduler GitHub async_postgres example](https://github.com/agronholm/apscheduler/blob/master/examples/standalone/async_postgres.py) - verified async PostgreSQL pattern (4.x, not directly applicable)
- [APScheduler 4.x Migration Guide](https://apscheduler.readthedocs.io/en/master/migration.html) - changes in 4.x, confirmed 4.x is still alpha
- [FastAPI + APScheduler Discussion](https://github.com/fastapi/fastapi/discussions/9143) - community patterns

### Tertiary (LOW confidence - needs validation)
- Medium articles on APScheduler + FastAPI integration - patterns verified against official docs
- Community discussions on multi-worker issues - confirmed in APScheduler issues tracker

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: APScheduler 3.x AsyncIOScheduler
- Ecosystem: tenacity for retry, FastAPI lifespan integration
- Patterns: lifespan integration, job definition, run history tracking
- Pitfalls: multi-worker, blocking event loop, missed jobs, memory leaks

**Confidence breakdown:**
- Standard stack: HIGH - APScheduler is well-documented, widely used
- Architecture: HIGH - patterns verified against official docs
- Pitfalls: HIGH - confirmed in GitHub issues and community discussions
- Code examples: HIGH - from official documentation

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - APScheduler 3.x is stable, patterns won't change)

</metadata>

---

*Phase: 05-scheduled-scraping*
*Research completed: 2026-01-20*
*Ready for planning: yes*
