"""Benchmark script for the scraping pipeline.

Runs a real scrape cycle, collects all progress events with timing data,
measures API response latency and memory usage, then produces a structured
markdown report at .planning/phases/53-investigation-benchmarking/BENCHMARK-BASELINE.md.

Usage:
    python scripts/benchmark_pipeline.py
"""

from __future__ import annotations

import asyncio
import os
import statistics
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on sys.path for src imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx
from sqlalchemy import select

from src.db.engine import async_session_factory
from src.db.models.scrape import ScrapeRun, ScrapeStatus
from src.db.models.settings import Settings
from src.scraping.clients import Bet9jaClient, BetPawaClient, SportyBetClient
from src.scraping.event_coordinator import EventCoordinator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def percentile(data: list[float], p: int) -> float:
    """Compute the p-th percentile of a list of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def fmt_ms(ms: int | float) -> str:
    """Format milliseconds as a string."""
    return f"{int(ms)}"


def pct(part: float, total: float) -> str:
    """Format a percentage."""
    if total == 0:
        return "N/A"
    return f"{(part / total) * 100:.1f}%"


# ---------------------------------------------------------------------------
# 1. Run a real scrape cycle
# ---------------------------------------------------------------------------

async def run_scrape_cycle() -> tuple[list[dict], int]:
    """Run a full EventCoordinator scrape cycle and collect all progress events.

    Returns:
        Tuple of (progress_events list, scrape_run_id).
    """
    progress_events: list[dict] = []

    async with async_session_factory() as db:
        # Get settings
        result = await db.execute(select(Settings).where(Settings.id == 1))
        settings = result.scalar_one_or_none()

        # Create ScrapeRun
        scrape_run = ScrapeRun(
            status=ScrapeStatus.RUNNING,
            trigger="benchmark",
        )
        db.add(scrape_run)
        await db.commit()
        await db.refresh(scrape_run)
        scrape_run_id = scrape_run.id

        # Create HTTP clients
        async with httpx.AsyncClient(
            base_url="https://www.sportybet.com",
            headers={
                "accept": "*/*",
                "accept-language": "en",
                "clientid": "web",
                "operid": "2",
                "platform": "web",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=50),
        ) as sportybet_http:
            async with httpx.AsyncClient(
                base_url="https://www.betpawa.ng",
                headers={
                    "accept": "*/*",
                    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                    "devicetype": "web",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "x-pawa-brand": "betpawa-nigeria",
                },
                timeout=30.0,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=50),
            ) as betpawa_http:
                async with httpx.AsyncClient(
                    base_url="https://sports.bet9ja.com",
                    headers={
                        "accept": "application/json, text/plain, */*",
                        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    },
                    timeout=30.0,
                    limits=httpx.Limits(max_connections=100, max_keepalive_connections=50),
                ) as bet9ja_http:

                    sportybet = SportyBetClient(sportybet_http)
                    betpawa = BetPawaClient(betpawa_http)
                    bet9ja = Bet9jaClient(bet9ja_http)

                    if settings:
                        coordinator = EventCoordinator.from_settings(
                            betpawa_client=betpawa,
                            sportybet_client=sportybet,
                            bet9ja_client=bet9ja,
                            settings=settings,
                        )
                    else:
                        coordinator = EventCoordinator(
                            betpawa_client=betpawa,
                            sportybet_client=sportybet,
                            bet9ja_client=bet9ja,
                        )

                    async for event in coordinator.run_full_cycle(
                        db=db, scrape_run_id=scrape_run_id
                    ):
                        progress_events.append(event)

        # Update scrape run status
        scrape_run.status = ScrapeStatus.COMPLETED
        scrape_run.completed_at = datetime.utcnow()
        await db.commit()

    return progress_events, scrape_run_id


# ---------------------------------------------------------------------------
# 2. Measure API response latency
# ---------------------------------------------------------------------------

async def measure_api_latency(
    base_url: str = "http://localhost:8000",
    runs: int = 5,
) -> dict[str, dict[str, float]] | None:
    """Measure API endpoint latencies.

    Returns:
        Dict mapping endpoint -> {p50, p95} in ms, or None if server not running.
    """
    endpoints = {
        "GET /api/events": "/api/events",
        "GET /api/events/{id}": "/api/events/1",
        "GET /api/scrape/runs": "/api/scrape/runs",
    }

    results: dict[str, list[float]] = {name: [] for name in endpoints}

    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            # Quick connectivity check
            try:
                await client.get("/api/events", params={"page_size": 1})
            except (httpx.ConnectError, httpx.ConnectTimeout):
                return None

            for name, path in endpoints.items():
                for _ in range(runs):
                    start = time.perf_counter()
                    try:
                        resp = await client.get(path)
                        elapsed_ms = (time.perf_counter() - start) * 1000

                        # For event detail, try to use a real event ID
                        if "{id}" in name and resp.status_code == 404:
                            # Try to find a real event ID from the list endpoint
                            list_resp = await client.get("/api/events", params={"page_size": 1})
                            if list_resp.status_code == 200:
                                data = list_resp.json()
                                events = data.get("events", [])
                                if events:
                                    real_id = events[0].get("id")
                                    if real_id:
                                        start = time.perf_counter()
                                        await client.get(f"/api/events/{real_id}")
                                        elapsed_ms = (time.perf_counter() - start) * 1000

                        results[name].append(elapsed_ms)
                    except Exception:
                        pass

    except Exception:
        return None

    # Compute percentiles
    latency: dict[str, dict[str, float]] = {}
    for name, timings in results.items():
        if timings:
            latency[name] = {
                "p50": round(percentile(timings, 50), 1),
                "p95": round(percentile(timings, 95), 1),
            }
        else:
            latency[name] = {"p50": 0, "p95": 0}

    return latency


# ---------------------------------------------------------------------------
# 3. Measure memory
# ---------------------------------------------------------------------------

def get_rss_mb() -> float | None:
    """Get current process RSS in MB. Returns None if not available."""
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        return round(proc.memory_info().rss / (1024 * 1024), 2)
    except ImportError:
        pass

    try:
        import resource
        # resource.getrusage returns maxrss in KB on Linux
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return round(usage.ru_maxrss / 1024, 2)
    except (ImportError, AttributeError):
        pass

    return None


# ---------------------------------------------------------------------------
# 4. Analyze progress events and produce report
# ---------------------------------------------------------------------------

def analyze_and_report(
    progress_events: list[dict],
    api_latency: dict[str, dict[str, float]] | None,
    peak_memory_mb: float,
    memory_delta_mb: float,
    rss_mb: float | None,
    total_wall_ms: int,
) -> str:
    """Analyze collected progress events and generate markdown report.

    Returns:
        Report content as a markdown string.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ---- Extract discovery data ----
    discovery_event = None
    for ev in progress_events:
        if ev.get("event_type") == "DISCOVERY_COMPLETE":
            discovery_event = ev
            break

    discovery_counts = discovery_event.get("discovery_counts", {}) if discovery_event else {}
    total_events_discovered = discovery_event.get("total_events", 0) if discovery_event else 0
    betpawa_disc_ms = discovery_event.get("betpawa_discovery_ms", 0) if discovery_event else 0
    sportybet_disc_ms = discovery_event.get("sportybet_discovery_ms", 0) if discovery_event else 0
    bet9ja_disc_ms = discovery_event.get("bet9ja_discovery_ms", 0) if discovery_event else 0
    discovery_total_ms = discovery_event.get("discovery_total_ms", 0) if discovery_event else 0

    # ---- Extract batch data ----
    batch_events = [ev for ev in progress_events if ev.get("event_type") == "BATCH_COMPLETE"]
    batch_count = len(batch_events)

    batch_scrape_times = [ev.get("batch_scrape_ms", 0) for ev in batch_events]
    batch_store_times = [ev.get("batch_store_ms", 0) for ev in batch_events]

    avg_batch_scrape = statistics.mean(batch_scrape_times) if batch_scrape_times else 0
    avg_batch_store = statistics.mean(batch_store_times) if batch_store_times else 0
    avg_batch_total = avg_batch_scrape + avg_batch_store

    storage_pct = pct(avg_batch_store, avg_batch_total) if avg_batch_total else "N/A"
    scrape_pct = pct(avg_batch_scrape, avg_batch_total) if avg_batch_total else "N/A"

    # Storage sub-phase breakdown (average across batches)
    storage_lookups = [ev.get("storage_lookups_ms", 0) for ev in batch_events]
    storage_processing = [ev.get("storage_processing_ms", 0) for ev in batch_events]
    storage_flush = [ev.get("storage_flush_ms", 0) for ev in batch_events]
    storage_commit = [ev.get("storage_commit_ms", 0) for ev in batch_events]

    avg_lookups = statistics.mean(storage_lookups) if storage_lookups else 0
    avg_processing = statistics.mean(storage_processing) if storage_processing else 0
    avg_flush = statistics.mean(storage_flush) if storage_flush else 0
    avg_commit = statistics.mean(storage_commit) if storage_commit else 0
    avg_storage_total = avg_lookups + avg_processing + avg_flush + avg_commit

    # ---- Extract per-event scraping data ----
    event_scraped = [ev for ev in progress_events if ev.get("event_type") == "EVENT_SCRAPED"]
    event_timings = [ev.get("timing_ms", 0) for ev in event_scraped]

    avg_event_time = statistics.mean(event_timings) if event_timings else 0
    p50_event_time = percentile(event_timings, 50) if event_timings else 0
    p95_event_time = percentile(event_timings, 95) if event_timings else 0

    # Platform timing distribution
    platform_timing_lists: dict[str, list[int]] = {}
    slowest_platform_counts: dict[str, int] = {}

    for ev in event_scraped:
        pt = ev.get("platform_timings", {})
        if not pt:
            continue
        # Track per-platform timings
        for platform, ms in pt.items():
            platform_timing_lists.setdefault(platform, []).append(ms)
        # Track slowest platform
        if pt:
            slowest = max(pt, key=pt.get)
            slowest_platform_counts[slowest] = slowest_platform_counts.get(slowest, 0) + 1

    slowest_platform = max(slowest_platform_counts, key=slowest_platform_counts.get) if slowest_platform_counts else "N/A"

    # ---- Extract cycle totals ----
    cycle_event = None
    for ev in progress_events:
        if ev.get("event_type") == "CYCLE_COMPLETE":
            cycle_event = ev
            break

    cycle_total_ms = cycle_event.get("total_timing_ms", 0) if cycle_event else total_wall_ms
    events_scraped_count = cycle_event.get("events_scraped", 0) if cycle_event else 0
    events_failed_count = cycle_event.get("events_failed", 0) if cycle_event else 0

    # ---- Compute time breakdown for bottleneck analysis ----
    total_scrape_time = sum(batch_scrape_times)
    total_store_time = sum(batch_store_times)
    # discovery_total_ms is wall-clock for parallel discovery

    pipeline_total = discovery_total_ms + total_scrape_time + total_store_time
    disc_pct_str = pct(discovery_total_ms, pipeline_total) if pipeline_total else "N/A"
    scrape_total_pct = pct(total_scrape_time, pipeline_total) if pipeline_total else "N/A"
    store_total_pct = pct(total_store_time, pipeline_total) if pipeline_total else "N/A"

    # Identify dominant sub-phase in storage
    storage_subphases = {
        "Lookups": avg_lookups,
        "Processing": avg_processing,
        "Flush": avg_flush,
        "Commit": avg_commit,
    }
    dominant_storage_subphase = max(storage_subphases, key=storage_subphases.get) if avg_storage_total > 0 else "N/A"

    # Bottleneck recommendation
    if pipeline_total > 0:
        disc_frac = discovery_total_ms / pipeline_total
        scrape_frac = total_scrape_time / pipeline_total
        store_frac = total_store_time / pipeline_total

        if store_frac > 0.5:
            bottleneck = "Storage"
            recommendation = "Phase 55 (Async Write Pipeline) is highest priority - storage dominates pipeline time"
        elif scrape_frac > 0.5:
            bottleneck = "Scraping"
            recommendation = "Phase 56 (Concurrency Tuning) is highest priority - scraping dominates pipeline time"
        elif disc_frac > 0.5:
            bottleneck = "Discovery"
            recommendation = "Phase 56 (Concurrency Tuning) should optimize discovery - discovery dominates pipeline time"
        else:
            bottleneck = "Mixed"
            recommendation = "No single dominant bottleneck. Phase 54 (Cache Layer) can reduce API latency; Phase 55 (Async Write Pipeline) can decouple storage"
    else:
        bottleneck = "Unknown"
        recommendation = "No measurements available"

    # ---- Build report ----
    lines = [
        "# Benchmark Baseline Report",
        "",
        f"**Date:** {now_str}",
        f"**Events discovered:** {total_events_discovered}",
        f"**Events scraped:** {events_scraped_count}",
        f"**Events failed:** {events_failed_count}",
        f"**Batches processed:** {batch_count}",
        f"**Total pipeline time:** {cycle_total_ms}ms ({cycle_total_ms / 1000:.1f}s)",
        "",
        "## Discovery Phase",
        "",
        "| Platform | Time (ms) | Events Found |",
        "|----------|-----------|--------------|",
        f"| BetPawa  | {fmt_ms(betpawa_disc_ms)} | {discovery_counts.get('betpawa', 0)} |",
        f"| SportyBet| {fmt_ms(sportybet_disc_ms)} | {discovery_counts.get('sportybet', 0)} |",
        f"| Bet9ja   | {fmt_ms(bet9ja_disc_ms)} | {discovery_counts.get('bet9ja', 0)} |",
        f"| **Total (wall-clock)** | **{fmt_ms(discovery_total_ms)}** | **{total_events_discovered} (merged)** |",
        "",
        "## Batch Processing",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Batch count | {batch_count} |",
        f"| Avg batch scrape time (ms) | {fmt_ms(avg_batch_scrape)} |",
        f"| Avg batch storage time (ms) | {fmt_ms(avg_batch_store)} |",
        f"| Storage % of total batch time | {storage_pct} |",
        f"| Scrape % of total batch time | {scrape_pct} |",
        "",
        "### Storage Breakdown (avg per batch)",
        "",
        "| Sub-phase | Time (ms) | % of Storage |",
        "|-----------|-----------|--------------|",
        f"| Lookups | {fmt_ms(avg_lookups)} | {pct(avg_lookups, avg_storage_total)} |",
        f"| Processing | {fmt_ms(avg_processing)} | {pct(avg_processing, avg_storage_total)} |",
        f"| Flush | {fmt_ms(avg_flush)} | {pct(avg_flush, avg_storage_total)} |",
        f"| Commit | {fmt_ms(avg_commit)} | {pct(avg_commit, avg_storage_total)} |",
        "",
        "## Per-Event Scraping",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Avg event scrape time (ms) | {fmt_ms(avg_event_time)} |",
        f"| P50 event scrape time (ms) | {fmt_ms(p50_event_time)} |",
        f"| P95 event scrape time (ms) | {fmt_ms(p95_event_time)} |",
        f"| Slowest platform (most often) | {slowest_platform} |",
        "",
        "### Platform Timing Distribution",
        "",
        "| Platform | Avg (ms) | P50 (ms) | P95 (ms) |",
        "|----------|----------|----------|----------|",
    ]

    for platform in ["betpawa", "sportybet", "bet9ja"]:
        timings = platform_timing_lists.get(platform, [])
        if timings:
            pavg = statistics.mean(timings)
            pp50 = percentile(timings, 50)
            pp95 = percentile(timings, 95)
            lines.append(f"| {platform.capitalize()} | {fmt_ms(pavg)} | {fmt_ms(pp50)} | {fmt_ms(pp95)} |")
        else:
            lines.append(f"| {platform.capitalize()} | N/A | N/A | N/A |")

    lines.extend([
        "",
        "## API Response Latency",
        "",
    ])

    if api_latency:
        lines.extend([
            "| Endpoint | P50 (ms) | P95 (ms) |",
            "|----------|----------|----------|",
        ])
        for endpoint, lat in api_latency.items():
            lines.append(f"| {endpoint} | {lat['p50']} | {lat['p95']} |")
    else:
        lines.append("*API latency: server not running, measure manually*")

    lines.extend([
        "",
        "## Memory",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Peak memory (MB) | {peak_memory_mb:.2f} |",
        f"| Memory delta (MB) | {memory_delta_mb:.2f} |",
    ])

    if rss_mb is not None:
        lines.append(f"| Process RSS (MB) | {rss_mb:.2f} |")

    lines.extend([
        "",
        "## Bottleneck Analysis",
        "",
        f"**Dominant cost center:** {bottleneck}",
        "",
        f"- Discovery: {disc_pct_str} of total pipeline time ({fmt_ms(discovery_total_ms)}ms)",
        f"- Scraping: {scrape_total_pct} of total pipeline time ({fmt_ms(total_scrape_time)}ms)",
        f"- Storage: {store_total_pct} of total pipeline time ({fmt_ms(total_store_time)}ms)",
        f"- Storage breakdown: {dominant_storage_subphase} dominates ({fmt_ms(storage_subphases.get(dominant_storage_subphase, 0))}ms avg per batch)",
        f"- **Recommendation:** {recommendation}",
        "",
        "### Phase Impact Mapping",
        "",
        "| v2.0 Phase | Addresses | Current Cost |",
        "|------------|-----------|-------------|",
        f"| Phase 54: Cache Layer | API response latency | {'Measured' if api_latency else 'Not measured (server down)'} |",
        f"| Phase 55: Async Write Pipeline | Storage bottleneck | {fmt_ms(total_store_time)}ms total |",
        f"| Phase 56: Concurrency Tuning | Scraping throughput | {fmt_ms(total_scrape_time)}ms total |",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    """Run benchmark and produce report."""
    print("=" * 60)
    print("  Pipeline Benchmark")
    print("=" * 60)
    print()

    # Start memory tracking
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    rss_before = get_rss_mb()

    # 1. Run scrape cycle
    print("[1/3] Running scrape cycle...")
    wall_start = time.perf_counter()

    try:
        progress_events, scrape_run_id = await run_scrape_cycle()
    except Exception as e:
        print(f"  ERROR: Scrape cycle failed: {e}")
        traceback.print_exc()
        return

    wall_ms = int((time.perf_counter() - wall_start) * 1000)
    print(f"  Scrape cycle complete in {wall_ms}ms (run #{scrape_run_id})")
    print(f"  Collected {len(progress_events)} progress events")

    # Memory snapshot after scrape
    snapshot_after = tracemalloc.take_snapshot()
    peak_current, peak_size = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_memory_mb = peak_size / (1024 * 1024)

    # Calculate delta from snapshots
    stats_diff = snapshot_after.compare_to(snapshot_before, "lineno")
    memory_delta_bytes = sum(stat.size_diff for stat in stats_diff)
    memory_delta_mb = memory_delta_bytes / (1024 * 1024)

    rss_after = get_rss_mb()
    rss_mb = rss_after

    print(f"  Peak memory: {peak_memory_mb:.2f} MB, delta: {memory_delta_mb:.2f} MB")

    # 2. Measure API latency
    print("[2/3] Measuring API latency...")
    api_latency = await measure_api_latency()
    if api_latency:
        print("  API latency measured successfully")
        for endpoint, lat in api_latency.items():
            print(f"    {endpoint}: p50={lat['p50']}ms, p95={lat['p95']}ms")
    else:
        print("  API server not running - skipping latency measurement")

    # 3. Generate report
    print("[3/3] Generating report...")

    report = analyze_and_report(
        progress_events=progress_events,
        api_latency=api_latency,
        peak_memory_mb=peak_memory_mb,
        memory_delta_mb=memory_delta_mb,
        rss_mb=rss_mb,
        total_wall_ms=wall_ms,
    )

    # Write report
    report_path = PROJECT_ROOT / ".planning" / "phases" / "53-investigation-benchmarking" / "BENCHMARK-BASELINE.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"  Report written to: {report_path}")
    print()

    # Print summary
    cycle_event = next((ev for ev in progress_events if ev.get("event_type") == "CYCLE_COMPLETE"), None)
    if cycle_event:
        print("Summary:")
        print(f"  Events scraped: {cycle_event.get('events_scraped', 0)}")
        print(f"  Events failed: {cycle_event.get('events_failed', 0)}")
        print(f"  Total time: {cycle_event.get('total_timing_ms', 0)}ms")
        print(f"  Batches: {cycle_event.get('batch_count', 0)}")

    print()
    print("Done!")


if __name__ == "__main__":
    import traceback
    asyncio.run(main())
