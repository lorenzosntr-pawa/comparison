"""Lightweight API latency benchmark for Phase 54 cache verification.

Measures GET /api/events and GET /api/events/{id} latency multiple times
and compares against Phase 53 baseline. Also fetches cache stats.

Usage:
    python scripts/benchmark_api_latency.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import httpx


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


# Phase 53 baseline values
BASELINE = {
    "GET /api/events": {"p50": 903.1, "p95": 2340.7},
    "GET /api/events/{id}": {"p50": 35.5, "p95": 37.7},
}


async def main() -> None:
    base_url = "http://localhost:8000"
    runs = 10  # More runs for statistical significance

    print("=" * 60)
    print("  Phase 54 API Latency Benchmark")
    print("=" * 60)
    print()

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Connectivity check
        try:
            resp = await client.get("/api/events", params={"page_size": 1})
            resp.raise_for_status()
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
            print(f"ERROR: Cannot reach API server at {base_url}: {e}")
            return

        # Find a real event ID for detail endpoint testing
        data = resp.json()
        events = data.get("events", [])
        real_event_id = events[0]["id"] if events else 1

        print(f"Running {runs} iterations per endpoint...")
        print(f"Using event_id={real_event_id} for detail endpoint")
        print()

        # Warm up (1 request each, not counted)
        await client.get("/api/events")
        await client.get(f"/api/events/{real_event_id}")

        # --- Benchmark GET /api/events ---
        list_timings: list[float] = []
        for i in range(runs):
            start = time.perf_counter()
            resp = await client.get("/api/events")
            elapsed_ms = (time.perf_counter() - start) * 1000
            list_timings.append(elapsed_ms)

        # --- Benchmark GET /api/events/{id} ---
        detail_timings: list[float] = []
        for i in range(runs):
            start = time.perf_counter()
            resp = await client.get(f"/api/events/{real_event_id}")
            elapsed_ms = (time.perf_counter() - start) * 1000
            detail_timings.append(elapsed_ms)

    # Compute results
    results = {
        "GET /api/events": {
            "p50": round(percentile(list_timings, 50), 1),
            "p95": round(percentile(list_timings, 95), 1),
            "min": round(min(list_timings), 1),
            "max": round(max(list_timings), 1),
        },
        "GET /api/events/{id}": {
            "p50": round(percentile(detail_timings, 50), 1),
            "p95": round(percentile(detail_timings, 95), 1),
            "min": round(min(detail_timings), 1),
            "max": round(max(detail_timings), 1),
        },
    }

    # Print results
    print("Results:")
    print("-" * 70)
    print(f"{'Endpoint':<25} {'Metric':<8} {'Baseline':<12} {'Now':<12} {'Change':<12}")
    print("-" * 70)

    for endpoint, metrics in results.items():
        baseline = BASELINE.get(endpoint, {})
        for pct_name in ["p50", "p95"]:
            base_val = baseline.get(pct_name, 0)
            new_val = metrics[pct_name]
            if base_val > 0:
                change_pct = ((new_val - base_val) / base_val) * 100
                change_str = f"{change_pct:+.1f}%"
            else:
                change_str = "N/A"
            print(
                f"{endpoint:<25} {pct_name:<8} {base_val:<12.1f} {new_val:<12.1f} {change_str:<12}"
            )
    print("-" * 70)
    print()

    # Target check
    list_p50 = results["GET /api/events"]["p50"]
    target_met = list_p50 < 450
    print(f"Target: GET /api/events p50 < 450ms")
    print(f"Actual: GET /api/events p50 = {list_p50}ms")
    print(f"Status: {'PASS' if target_met else 'FAIL'}")
    print()

    # Raw timings
    print("Raw timings (ms):")
    print(f"  GET /api/events:      {[round(t, 1) for t in list_timings]}")
    print(f"  GET /api/events/{{id}}: {[round(t, 1) for t in detail_timings]}")


if __name__ == "__main__":
    asyncio.run(main())
