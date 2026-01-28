# Phase 34: Investigation & Matching Audit Report - Context

**Gathered:** 2026-01-28
**Status:** Ready for planning

<vision>
## How This Should Work

A comprehensive investigation combining **code audit** and **data analysis** to understand why event matching across platforms is broken.

**Architecture-first approach:** Start by documenting how the system SHOULD work (all platforms linked via SportRadar ID), then systematically map where the current implementation deviates from that ideal.

**Root cause hypothesis:** The issues likely stem from the v1.1 transition — the project started Betpawa-centric (scrape Betpawa, store competitor JSON alongside), then added full competitor palimpsest scraping with separate tables (`competitor_events`, `competitor_odds_snapshots`). This created a hybrid system where the old and new approaches may not be properly integrated.

**Known symptoms:**
- Missing matches (events exist on all 3 platforms but aren't linked)
- Wrong pairings (events matched to wrong counterparts)
- Inconsistent SportRadar ID extraction
- Missing `scraper_run` references in `competitor_odds_snapshots`

**Deliverable format:**
1. How the system SHOULD work (ideal architecture)
2. How it ACTUALLY works (current state)
3. Specific deviations/bugs with evidence
4. Recommendation: patch the hybrid system vs. refactor toward unified approach

</vision>

<essential>
## What Must Be Nailed

- **Clear fix roadmap** — Phases 35-37 should be unambiguous after this investigation
- **Architecture decision** — Patch the hybrid system or refactor it? Investigation provides the answer.
- **Scope clarity** — Is this small fixes or major rework? Understand the true size of the problem.

</essential>

<boundaries>
## What's Out of Scope

- No code changes — this is pure investigation, all fixes happen in Phase 35+
- No new features — don't scope-creep into improving matching beyond what's broken
- No DB migrations — document schema issues but don't change the schema yet
- No rabbit holes — time-boxed, symptom-focused, actionable findings only

</boundaries>

<specifics>
## Specific Areas to Audit

**Code analysis:**
- SportRadar ID extraction per platform (Sporty URL-encoded `sr:match:id`, Betpawa widgets, Bet9ja `extid`)
- Schema relationships (how `competitor_events`/`odds` link to Betpawa events and `scraper_runs`)
- Query-time matching logic
- Full pipeline: match linking → odds linking → scraper run linking

**Data analysis:**
- Sample specific mismatches (events that should match but don't, with IDs shown)
- Aggregate statistics (match rates, ID extraction rates per platform)
- Demonstrate issues with actual SQL queries

**Output:**
- Ensure fresh odds per bookmaker are correctly associated with each matched event

</specifics>

<notes>
## Additional Context

**Keep investigation bounded:**
- Time-box the analysis — capture findings, move on even if not 100% complete
- Focus on known symptoms — don't hunt for theoretical problems
- Only document actionable issues — skip things without a clear fix path

**Architecture direction:**
- No predetermined preference — let the findings guide whether to patch or refactor
- Ideal state: all platforms linked purely via SportRadar ID (no Betpawa anchor required)

</notes>

---

*Phase: 34-investigation-matching-audit*
*Context gathered: 2026-01-28*
