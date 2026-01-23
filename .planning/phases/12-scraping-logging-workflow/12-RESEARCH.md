# Phase 14: Scraping Logging & Workflow - Research

**Researched:** 2026-01-22
**Domain:** Python async workflow state management, structured logging, FastAPI SSE
**Confidence:** HIGH

<research_summary>
## Summary

Researched patterns for improving scraping workflow visibility, structured logging, and state management in the existing FastAPI + SQLAlchemy + SSE stack. The codebase already has solid foundations (ProgressBroadcaster, ScrapeRun model, SSE streaming), but lacks granular state tracking and structured logging.

The recommended approach is evolutionary, not revolutionary:
1. **Extend existing models** (ScrapeRun, ScrapeProgress) with granular phase/state fields
2. **Add structlog** for structured JSON logging with context propagation
3. **Persist state transitions** to database for audit trail and restart recovery
4. **Enhance SSE streaming** with richer phase data and error context

No external state machine library needed — the workflow is simple enough (3 platforms, linear phases) that StrEnum + explicit transitions are cleaner than a full state machine framework.

**Primary recommendation:** Use structlog for JSON logging with contextvars, extend ScrapeRun model with phase tracking fields, create ScrapePhaseLog table for state history, and enhance SSE messages with structured error context.
</research_summary>

<standard_stack>
## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.109+ | Web framework | Already in project, excellent async support |
| SQLAlchemy | 2.x | ORM | Already in project, async-first with 2.0 |
| APScheduler | 3.x | Background jobs | Already in project, handles scheduling |

### Add for This Phase
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| structlog | 24.x | Structured logging | Industry standard for JSON logs, native contextvars support |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| StrEnum | builtin | Status/phase enums | Type-safe state representation |
| asyncio | builtin | Async concurrency | Existing orchestrator pattern |
| contextvars | builtin | Request-scoped context | Already used implicitly by async |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| structlog | python-json-logger | structlog has better contextvars integration |
| Custom state tracking | pytransitions | Overkill for linear workflow with 3 platforms |
| SSE polling | WebSockets | SSE is simpler, already working, unidirectional is fine |
| Database state | Redis | Database provides persistence + audit trail |

**Installation:**
```bash
pip install structlog
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Additions to Project Structure
```
src/
├── scraping/
│   ├── orchestrator.py       # Enhance with phase emissions
│   ├── broadcaster.py        # Enhance with state persistence
│   ├── schemas.py            # Add ScrapePhase enum, enhance ScrapeProgress
│   └── logging.py            # NEW: structlog configuration
├── db/models/
│   └── scrape.py             # Enhance ScrapeRun, add ScrapePhaseLog
└── api/routes/
    └── scrape.py             # Enhance SSE with richer data
```

### Pattern 1: Granular Phase Enum
**What:** Use StrEnum for explicit scrape phases, not generic strings
**When to use:** State tracking where finite, known states exist
**Example:**
```python
from enum import StrEnum

class ScrapePhase(StrEnum):
    """Granular scrape workflow phases."""
    # Overall workflow
    INITIALIZING = "initializing"

    # Per-platform phases (prefix with platform)
    DISCOVERING = "discovering"      # Finding competitions/events
    SCRAPING = "scraping"            # Fetching event data
    MAPPING = "mapping"              # Mapping markets to BetPawa format
    STORING = "storing"              # Writing to database

    # Terminal phases
    COMPLETED = "completed"
    FAILED = "failed"


class PlatformStatus(StrEnum):
    """Per-platform status within a scrape run."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
```

### Pattern 2: State History Table
**What:** Persist phase transitions for audit trail and restart recovery
**When to use:** Need to know what happened, not just current state
**Example:**
```python
class ScrapePhaseLog(Base):
    """Audit log of phase transitions during a scrape run."""
    __tablename__ = "scrape_phase_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scrape_run_id: Mapped[int] = mapped_column(ForeignKey("scrape_runs.id"))
    platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phase: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    events_processed: Mapped[int | None] = mapped_column(nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

### Pattern 3: Structlog with Contextvars
**What:** Structured logging with automatic context propagation
**When to use:** Async applications needing request/task scoped logging
**Example:**
```python
import structlog
from contextvars import ContextVar

# Context for current scrape run
scrape_context: ContextVar[dict] = ContextVar("scrape_context", default={})

def configure_structlog():
    """Configure structlog for JSON output with context."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

# Usage in orchestrator
async def _scrape_platform(self, platform: Platform, ...):
    structlog.contextvars.bind_contextvars(
        scrape_run_id=scrape_run_id,
        platform=platform.value,
    )
    logger = structlog.get_logger()
    logger.info("starting_platform_scrape", phase="scraping")
```

### Pattern 4: Enhanced SSE Progress Schema
**What:** Richer progress messages with timing, counts, and error context
**When to use:** Real-time UI updates needing detailed status
**Example:**
```python
class ScrapeProgress(BaseModel):
    """Enhanced scrape progress for SSE streaming."""
    # Identification
    scrape_run_id: int
    platform: Platform | None

    # Phase tracking
    phase: ScrapePhase
    sub_phase: str | None = None  # e.g., "competition_5_of_12"

    # Progress metrics
    current: int
    total: int
    events_count: int = 0

    # Timing
    started_at: datetime
    elapsed_ms: int
    estimated_remaining_ms: int | None = None

    # Status message
    message: str

    # Error context (if phase == FAILED)
    error: ScrapeErrorContext | None = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ScrapeErrorContext(BaseModel):
    """Structured error information for UI display."""
    error_type: str  # "timeout", "network", "parse", "storage"
    error_message: str
    recoverable: bool
    retry_suggested: bool
```

### Pattern 5: Per-Platform Status Tracking
**What:** Explicit platform status field on ScrapeRun, not inferred from platform_timings
**When to use:** Need instant visibility into which platforms are active/done/failed
**Example:**
```python
# Add to ScrapeRun model
platform_status: Mapped[dict | None] = mapped_column(JSON, nullable=True)
# Format: {"betpawa": "completed", "sportybet": "active", "bet9ja": "pending"}

current_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
current_platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

### Anti-Patterns to Avoid
- **Inferring state from absence:** Don't infer "active" from missing platform_timings — track explicitly
- **Generic phase strings:** Don't use arbitrary strings — use ScrapePhase enum for validation
- **Logging after completion:** Don't wait until scrape ends to log errors — log immediately
- **State machine library for simple flow:** pytransitions/python-statemachine are overkill for 3 platforms with linear phases
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON structured logging | Custom JSON formatter | structlog | Handles contextvars, processors, output formats properly |
| Request-scoped context | Manual context passing | contextvars module | Built-in, async-safe, structlog integrates natively |
| Timestamp formatting | Custom ISO string conversion | structlog.processors.TimeStamper | Handles timezone, format, precision correctly |
| Log level filtering | if logger.level checks | structlog.make_filtering_bound_logger | Proper level hierarchy, configurable |

**Key insight:** The logging improvements are well-served by structlog. The state tracking improvements are model/schema changes to existing patterns — no new libraries needed. Don't add pytransitions or python-statemachine for a workflow with only 3 platforms and 5 phases per platform.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Context Lost in Background Tasks
**What goes wrong:** Contextvars set in route handler not available in scheduled job
**Why it happens:** APScheduler runs jobs in different contexts than HTTP requests
**How to avoid:** Bind context explicitly at the start of each scrape job:
```python
async def scrape_job():
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        job_type="scheduled_scrape",
        scrape_run_id=run.id,
    )
```
**Warning signs:** Logs missing scrape_run_id or showing stale IDs

### Pitfall 2: SSE State Sync Race Conditions
**What goes wrong:** UI shows stale state because DB update and SSE message not atomic
**Why it happens:** Broadcast happens before/after DB commit
**How to avoid:** Update DB state BEFORE broadcasting, and include DB timestamp in SSE message
**Warning signs:** UI flickers between states, late subscribers see inconsistent state

### Pitfall 3: Platform Timings Incomplete for Failed Platforms
**What goes wrong:** Failed platforms have no entry in platform_timings, UI can't display them
**Why it happens:** Timings only written on success
**How to avoid:** Use separate platform_status field, write timings even for failures (with error flag)
**Warning signs:** Platform breakdown in UI omits failed platforms entirely

### Pitfall 4: Blocking Event Loop with Synchronous Logging
**What goes wrong:** High log volume causes response latency spikes
**Why it happens:** Default logging handlers are synchronous
**How to avoid:** Use structlog with async-compatible output (stdout in container environments) or queue handlers
**Warning signs:** P99 latency increases when scraping active

### Pitfall 5: Lost Phase History on Restart
**What goes wrong:** If backend restarts mid-scrape, no way to know what phase it was in
**Why it happens:** Phase stored only in memory (ProgressBroadcaster), not DB
**How to avoid:** Write phase transitions to ScrapePhaseLog table as they happen
**Warning signs:** Scrape shows "unknown state" after restart
</common_pitfalls>

<code_examples>
## Code Examples

### Configure Structlog for FastAPI
```python
# src/scraping/logging.py
import logging
import structlog
from structlog.typing import FilteringBoundLogger

def configure_logging(json_output: bool = True) -> None:
    """Configure structlog with JSON output and context propagation."""

    # Set up shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Human-readable colored output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Usage
logger = structlog.get_logger()
```

### Enhanced ScrapeProgress Schema
```python
# src/scraping/schemas.py
from enum import StrEnum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ScrapePhase(StrEnum):
    """Scrape workflow phases."""
    INITIALIZING = "initializing"
    DISCOVERING = "discovering"
    SCRAPING = "scraping"
    MAPPING = "mapping"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"

class PlatformStatus(StrEnum):
    """Platform status within a scrape run."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapeErrorContext(BaseModel):
    """Structured error info for UI display."""
    error_type: str
    error_message: str
    platform: str | None = None
    recoverable: bool = False

class ScrapeProgress(BaseModel):
    """Enhanced progress for SSE streaming."""
    scrape_run_id: int | None = None
    platform: Platform | None = None
    phase: ScrapePhase

    # Progress metrics
    current: int
    total: int
    events_count: int = 0

    # Timing
    elapsed_ms: int | None = None

    # Human-readable message
    message: str

    # Error context (populated when phase == FAILED)
    error: ScrapeErrorContext | None = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### State Persistence in Orchestrator
```python
# Pseudocode for enhanced orchestrator

async def _emit_phase(
    self,
    db: AsyncSession,
    scrape_run_id: int,
    platform: Platform | None,
    phase: ScrapePhase,
    message: str,
    events_count: int = 0,
    error: ScrapeErrorContext | None = None,
) -> None:
    """Emit phase transition to both DB and SSE."""
    # 1. Update ScrapeRun current state
    await db.execute(
        update(ScrapeRun)
        .where(ScrapeRun.id == scrape_run_id)
        .values(
            current_phase=phase.value,
            current_platform=platform.value if platform else None,
        )
    )

    # 2. Log to phase history
    phase_log = ScrapePhaseLog(
        scrape_run_id=scrape_run_id,
        platform=platform.value if platform else None,
        phase=phase.value,
        events_processed=events_count,
        message=message,
        error_details=error.model_dump() if error else None,
    )
    db.add(phase_log)
    await db.flush()

    # 3. Broadcast via SSE
    progress = ScrapeProgress(
        scrape_run_id=scrape_run_id,
        platform=platform,
        phase=phase,
        current=self._completed_platforms,
        total=len(self._target_platforms),
        events_count=events_count,
        message=message,
        error=error,
    )
    await self._broadcaster.publish(progress)

    # 4. Structured log
    logger.info(
        "phase_transition",
        scrape_run_id=scrape_run_id,
        platform=platform.value if platform else None,
        phase=phase.value,
        events_count=events_count,
    )
```

### Dashboard Widget Row Enhancement
```tsx
// Pseudocode for enhanced scrape run row

interface ScrapeRunRow {
  id: number;
  status: ScrapeStatus;
  currentPhase?: string;
  currentPlatform?: string;
  platformStatus: Record<string, 'pending' | 'active' | 'completed' | 'failed'>;
  elapsedMs: number;
  eventsScraped: number;
  errorCount: number;
  errorSummary?: string;
}

// Display logic
function ScrapeRunRowDisplay({ run }: { run: ScrapeRunRow }) {
  return (
    <div>
      {/* Status badge */}
      <StatusBadge status={run.status} />

      {/* Per-platform mini-status */}
      <div className="flex gap-1">
        {Object.entries(run.platformStatus).map(([platform, status]) => (
          <PlatformStatusIcon key={platform} platform={platform} status={status} />
        ))}
      </div>

      {/* Current activity (for running scrapes) */}
      {run.status === 'running' && (
        <span className="text-muted-foreground">
          {run.currentPlatform}: {run.currentPhase}...
        </span>
      )}

      {/* Timing */}
      <span>{formatDuration(run.elapsedMs)}</span>

      {/* Error indicator */}
      {run.errorCount > 0 && (
        <span className="text-destructive">{run.errorCount} errors</span>
      )}
    </div>
  );
}
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| stdlib logging + json formatter | structlog | Mature since 2020 | Better context propagation, cleaner API |
| Thread-local context | contextvars | Python 3.7+ | Async-safe context for asyncio |
| StrEnum backport | builtin StrEnum | Python 3.11 | No external dependency needed |

**New tools/patterns to consider:**
- **structlog 24.x:** Improved async performance, better typing support
- **contextvars in APScheduler:** Jobs can inherit context from caller if properly configured

**Deprecated/outdated:**
- **logging.config.dictConfig for JSON:** Use structlog instead — cleaner API
- **Thread-local for async context:** Doesn't work with asyncio — use contextvars
</sota_updates>

<open_questions>
## Open Questions

1. **Database migration strategy**
   - What we know: Need to add fields to ScrapeRun and create ScrapePhaseLog table
   - What's unclear: Can we add nullable fields to avoid data migration for existing rows?
   - Recommendation: Add all new fields as nullable, backfill not required for historical data

2. **SSE reconnection handling**
   - What we know: EventSource auto-reconnects, broadcaster has "catch up" for latest state
   - What's unclear: Should we send full history on reconnect or just latest?
   - Recommendation: Send latest state on reconnect (current behavior), phase history available via API

3. **Timing estimation accuracy**
   - What we know: Can calculate elapsed time, know event counts
   - What's unclear: How to estimate remaining time accurately (platform speeds vary)
   - Recommendation: Don't estimate remaining — just show elapsed and per-platform counts
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- Current codebase analysis: orchestrator.py, broadcaster.py, scrape.py models
- [structlog documentation](https://www.structlog.org/en/stable/contextvars.html) - contextvars integration
- [Python enum documentation](https://docs.python.org/3/howto/enum.html) - StrEnum patterns

### Secondary (MEDIUM confidence)
- [FastAPI structlog integration guide](https://wazaari.dev/blog/fastapi-structlog-integration) - middleware patterns
- [Better Stack FastAPI logging guide](https://betterstack.com/community/guides/logging/logging-with-fastapi/) - best practices

### Tertiary (LOW confidence - needs validation)
- N/A - all findings verified with current codebase
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: FastAPI + SQLAlchemy async workflow enhancement
- Ecosystem: structlog, Python stdlib (contextvars, StrEnum)
- Patterns: Phase enums, state history tables, structured logging
- Pitfalls: Context propagation, SSE sync, background task context

**Confidence breakdown:**
- Standard stack: HIGH - existing stack sufficient, only add structlog
- Architecture: HIGH - patterns derived from current codebase analysis
- Pitfalls: HIGH - identified from current implementation gaps
- Code examples: HIGH - based on current codebase patterns

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable patterns)
</metadata>

---

*Phase: 14-scraping-logging-workflow*
*Research completed: 2026-01-22*
*Ready for planning: yes*
