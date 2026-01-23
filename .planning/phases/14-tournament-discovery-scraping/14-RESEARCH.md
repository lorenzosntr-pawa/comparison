# Phase 14: Tournament Discovery Scraping - Research

**Researched:** 2026-01-23
**Domain:** Competitor API tournament listing (SportyBet, Bet9ja)
**Confidence:** HIGH

<research_summary>
## Summary

Researched the SportyBet and Bet9ja APIs to understand tournament listing endpoints, data structures, and integration patterns with the existing scraper infrastructure.

Key finding: Both APIs return complete tournament hierarchies in single requests - no pagination needed. SportyBet uses SportRadar IDs natively at tournament level, while Bet9ja uses internal IDs only (no SR IDs for tournaments). The existing `Bet9jaClient.fetch_sports()` method already retrieves the tournament hierarchy; SportyBet needs a new `fetch_tournaments()` method.

**Primary recommendation:** Extend existing scraper clients with tournament discovery methods. Create a separate `TournamentDiscoveryService` to handle tournament upsert logic into CompetitorTournament model. Reuse existing patterns for retry, error handling, and logging.
</research_summary>

<standard_stack>
## Standard Stack

### Core (Already in codebase)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.27+ | Async HTTP client | Already used for all scraping |
| tenacity | 8.2+ | Retry logic | Already configured in base.py |
| structlog | 24.1+ | Structured logging | Already used throughout |
| SQLAlchemy | 2.0+ | Async ORM | Already used for all models |

### Existing Infrastructure to Reuse
| Component | Location | Purpose |
|-----------|----------|---------|
| `Bet9jaClient.fetch_sports()` | `src/scraping/clients/bet9ja.py:169-212` | Returns full sport/tournament hierarchy - reuse directly |
| `SportyBetClient` | `src/scraping/clients/sportybet.py` | Extend with new tournament listing method |
| `CompetitorTournament` model | `src/db/models/competitor.py:23-55` | Already created in Phase 13 |
| `create_retry_decorator()` | `src/scraping/clients/base.py:43-60` | Reuse for new methods |
| `ScrapingOrchestrator` | `src/scraping/orchestrator.py` | Pattern reference, may need new orchestrator |

### No New Dependencies Needed
Tournament discovery uses existing scraper infrastructure. No new libraries required.
</standard_stack>

<api_structures>
## API Structures

### SportyBet Tournament Listing

**Endpoint:** `GET /api/ng/factsCenter/popularAndSportList`

**Parameters:**
```
sportId=sr:sport:1    # Football
timeline=             # Empty for all
productId=3           # Required
_t={timestamp_ms}     # Cache buster
```

**Response structure:**
```json
{
  "bizCode": 10000,
  "message": "0#0",
  "data": {
    "sportList": [
      {
        "id": "sr:sport:1",
        "name": "Football",
        "eventSize": 1414,
        "categories": [
          {
            "id": "sr:category:304",
            "name": "Algeria",
            "eventSize": 17,
            "tournaments": [
              {
                "id": "sr:tournament:841",
                "name": "Ligue 1",
                "eventSize": 5
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Key fields:**
- `category.id` - SportRadar category ID (e.g., `sr:category:304`)
- `category.name` - Country/region name
- `tournament.id` - SportRadar tournament ID (e.g., `sr:tournament:841`)
- `tournament.name` - Tournament display name
- `tournament.eventSize` - Number of events (informational)

**Notes:**
- Uses SportRadar IDs natively
- Single request returns ALL football tournaments
- No pagination required
- Response size: ~100KB for 200+ tournaments

### Bet9ja Tournament Listing

**Endpoint:** `GET /desktop/feapi/PalimpsestAjax/GetSports` (already implemented)

**Parameters:**
```
DISP=0
v_cache_version=1.301.2.225
```

**Response structure:**
```json
{
  "R": "OK",
  "D": {
    "PAL": {
      "1": {                              // Sport ID (1 = Soccer)
        "S_DESC": "Soccer",
        "NUM": 861,
        "SG": {                           // SubGroups (countries)
          "11058": {                      // SubGroup ID
            "SG_DESC": "England",
            "NUM": 125,
            "G": {                        // Groups (tournaments)
              "170880": {                 // Tournament ID
                "G_DESC": "Premier League",
                "NUM": 21
              },
              "170881": {
                "G_DESC": "Championship",
                "NUM": 24
              }
            }
          }
        }
      }
    }
  }
}
```

**Key fields:**
- `PAL.1` - Soccer sport
- `SG.{id}` - Country/region subgroup
- `SG.{id}.SG_DESC` - Country name
- `G.{id}` - Tournament (key is tournament ID)
- `G.{id}.G_DESC` - Tournament display name
- `G.{id}.NUM` - Number of events (informational)

**Notes:**
- NO SportRadar IDs at tournament level
- Internal IDs only (170880 = Premier League)
- Single request returns ALL sports and tournaments
- Response size: ~400KB for full hierarchy
- Filter to `PAL.1` for Soccer only
</api_structures>

<architecture_patterns>
## Architecture Patterns

### Data Flow
```
SportyBet API ─────┐
                   │     TournamentDiscoveryService     CompetitorTournament
Bet9ja API ────────┼───> (normalize + upsert)  ──────> (database model)
                   │
```

### Service Architecture
Create a dedicated `TournamentDiscoveryService` rather than extending `ScrapingOrchestrator`:

```
src/
├── scraping/
│   ├── clients/
│   │   ├── sportybet.py    # Add fetch_tournaments() method
│   │   └── bet9ja.py       # fetch_sports() already exists
│   └── tournament_discovery.py  # NEW: TournamentDiscoveryService
```

**Why separate service:**
- Tournament discovery is a distinct operation from event scraping
- Different frequency (less often than event scraping)
- Different data flow (tournaments → CompetitorTournament, not Event)
- Simpler orchestration (no cross-platform ID dependency)

### Model Mapping

**SportyBet → CompetitorTournament:**
```python
CompetitorTournament(
    source=CompetitorSource.SPORTYBET,
    sport_id=1,  # Football
    name=tournament["name"],           # "Premier League"
    country_raw=category["name"],      # "England"
    external_id=tournament["id"],      # "sr:tournament:17" (full SR ID)
    sportradar_id=tournament["id"].replace("sr:tournament:", ""),  # "17"
)
```

**Bet9ja → CompetitorTournament:**
```python
CompetitorTournament(
    source=CompetitorSource.BET9JA,
    sport_id=1,  # Football
    name=g_data["G_DESC"],             # "Premier League"
    country_raw=sg_data["SG_DESC"],    # "England"
    external_id=g_id,                  # "170880"
    sportradar_id=None,                # No SR ID at tournament level
)
```

### Upsert Pattern
Use source + external_id as unique key (already has DB constraint):

```python
# Check existing
existing = await db.execute(
    select(CompetitorTournament).where(
        CompetitorTournament.source == source,
        CompetitorTournament.external_id == external_id,
    )
)
tournament = existing.scalar_one_or_none()

if tournament:
    # Update name, country if changed
    tournament.name = name
    tournament.country_raw = country_raw
else:
    # Insert new
    tournament = CompetitorTournament(...)
    db.add(tournament)
```
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP requests with retry | Custom retry loops | `tenacity` + `create_retry_decorator()` | Edge cases, exponential backoff, exception filtering |
| Response validation | Manual checks | Pydantic or existing validation patterns | Type safety, clear errors |
| Tournament upsert | Raw SQL | SQLAlchemy ORM with unique constraint | DB handles race conditions |
| API headers/auth | Manual construction | Existing client patterns | Already tested, includes required headers |
| Sport ID lookup | Hardcode magic numbers | Query Sports table | Consistent with codebase |

**Key insight:** Phase 14 is primarily about data extraction and normalization. All the infrastructure (HTTP, retry, ORM, models) is already in place from v1.0 and Phase 13.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Assuming SR IDs Exist Everywhere
**What goes wrong:** Code expects `sportradar_id` on all tournaments, fails for Bet9ja
**Why it happens:** SportyBet has SR IDs, assumption it's universal
**How to avoid:** Model already has `sportradar_id` as nullable. Handle None gracefully.
**Warning signs:** NullPointerException when accessing tournament.sportradar_id for Bet9ja records

### Pitfall 2: Country Name Inconsistency
**What goes wrong:** Same country has different names: "England" vs "United Kingdom" vs "UK"
**Why it happens:** Each platform uses their own naming conventions
**How to avoid:** Store in `country_raw`, defer normalization. Don't try to match tournaments by country name.
**Warning signs:** Tournament matching fails because country names differ

### Pitfall 3: Over-Engineering Scheduling
**What goes wrong:** Building complex scheduler for tournament discovery
**Why it happens:** Thinking it needs same frequency as event scraping
**How to avoid:** Tournament lists change rarely. Manual trigger or daily cron is sufficient.
**Warning signs:** Building scheduler integration before basic discovery works

### Pitfall 4: Trying to Match Tournaments Across Platforms
**What goes wrong:** Attempting to link SportyBet Premier League to Bet9ja Premier League
**Why it happens:** Natural desire to unify data
**How to avoid:** Context says "Don't try to match tournaments across platforms. SR IDs aren't available at tournament level. Infer tournament relationships from event matching later."
**Warning signs:** Building complex name-matching heuristics for tournaments
</common_pitfalls>

<code_examples>
## Code Examples

### SportyBet Client Extension
```python
# Add to src/scraping/clients/sportybet.py

@_retry
async def fetch_tournaments(self, sport_id: str = "sr:sport:1") -> dict:
    """Fetch tournament hierarchy from SportyBet API.

    Args:
        sport_id: SportRadar sport ID (default: football).

    Returns:
        Full API response with sportList containing categories and tournaments.
    """
    params = {
        "sportId": sport_id,
        "timeline": "",
        "productId": "3",
        "_t": str(int(time.time() * 1000)),
    }

    try:
        response = await self._client.get(
            f"{BASE_URL}/api/ng/factsCenter/popularAndSportList",
            params=params,
            headers=HEADERS,
        )
        response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        raise NetworkError(f"Network error fetching tournaments: {e}", cause=e) from e

    data = response.json()

    if data.get("bizCode") != 10000:
        raise ApiError(
            f"bizCode={data.get('bizCode')}: {data.get('message', 'Unknown error')}",
            details={"response": data},
        )

    return data
```

### Tournament Discovery Service
```python
# src/scraping/tournament_discovery.py

class TournamentDiscoveryService:
    """Discovers and stores competitor tournaments."""

    async def discover_sportybet_tournaments(
        self,
        client: SportyBetClient,
        db: AsyncSession,
    ) -> tuple[int, int]:
        """Discover all SportyBet football tournaments.

        Returns:
            Tuple of (new_count, updated_count).
        """
        data = await client.fetch_tournaments()

        new_count = 0
        updated_count = 0

        sport_list = data.get("data", {}).get("sportList", [])
        for sport in sport_list:
            if sport.get("id") != "sr:sport:1":  # Football only
                continue

            for category in sport.get("categories", []):
                country_name = category.get("name")

                for tournament in category.get("tournaments", []):
                    sr_id = tournament["id"]  # e.g., "sr:tournament:17"
                    sr_id_num = sr_id.replace("sr:tournament:", "")

                    new, updated = await self._upsert_tournament(
                        db=db,
                        source=CompetitorSource.SPORTYBET,
                        external_id=sr_id,
                        name=tournament["name"],
                        country_raw=country_name,
                        sportradar_id=sr_id_num,
                    )
                    new_count += new
                    updated_count += updated

        await db.commit()
        return new_count, updated_count
```

### Bet9ja Tournament Extraction
```python
async def discover_bet9ja_tournaments(
    self,
    client: Bet9jaClient,
    db: AsyncSession,
) -> tuple[int, int]:
    """Discover all Bet9ja football tournaments.

    Returns:
        Tuple of (new_count, updated_count).
    """
    data = await client.fetch_sports()

    new_count = 0
    updated_count = 0

    # Navigate: D.PAL.1 (Soccer)
    soccer = data.get("D", {}).get("PAL", {}).get("1", {})
    sport_groups = soccer.get("SG", {})

    for sg_id, sg_data in sport_groups.items():
        country_name = sg_data.get("SG_DESC")
        tournaments = sg_data.get("G", {})

        for g_id, g_data in tournaments.items():
            new, updated = await self._upsert_tournament(
                db=db,
                source=CompetitorSource.BET9JA,
                external_id=g_id,
                name=g_data.get("G_DESC"),
                country_raw=country_name,
                sportradar_id=None,  # No SR ID at tournament level
            )
            new_count += new
            updated_count += updated

    await db.commit()
    return new_count, updated_count
```
</code_examples>

<verification_criteria>
## Verification Criteria

Phase 14 is complete when:

1. **SportyBet tournaments discoverable:**
   - `SportyBetClient.fetch_tournaments()` returns valid data
   - All football categories and tournaments parsed
   - SportRadar IDs captured

2. **Bet9ja tournaments discoverable:**
   - Existing `fetch_sports()` used to extract tournaments
   - All football tournaments from PAL.1.SG.*.G parsed

3. **Data stored correctly:**
   - CompetitorTournament records created for both sources
   - source, external_id, name, country_raw populated
   - sportradar_id populated for SportyBet, NULL for Bet9ja

4. **Upsert logic works:**
   - Running discovery twice doesn't create duplicates
   - Changed tournament names get updated

5. **Database queryable:**
   ```sql
   SELECT source, COUNT(*) FROM competitor_tournaments GROUP BY source;
   -- Should show counts for both sportybet and bet9ja

   SELECT * FROM competitor_tournaments WHERE source = 'sportybet' LIMIT 5;
   -- Should show SportRadar IDs

   SELECT * FROM competitor_tournaments WHERE source = 'bet9ja' LIMIT 5;
   -- sportradar_id should be NULL
   ```
</verification_criteria>

<open_questions>
## Open Questions

1. **Scheduling frequency?**
   - What we know: Tournament lists change slowly (new competitions start seasonally)
   - What's unclear: Whether to integrate with scheduler or keep as manual operation
   - Recommendation: Start with manual API endpoint, add scheduling later if needed

2. **Sport table integration?**
   - What we know: CompetitorTournament has sport_id FK to sports table
   - What's unclear: Is "Football" sport already seeded? What ID?
   - Recommendation: Query or create sport record before tournament discovery

3. **Event count accuracy?**
   - What we know: Both APIs return event counts (eventSize, NUM)
   - What's unclear: Whether to store these counts (may be stale quickly)
   - Recommendation: Don't store - query live when needed
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `api_route_sporty/get_all tournaments/response.json` - Captured SportyBet API response
- `api_route_sporty/get_all tournaments/header.txt` - Request details and endpoint
- `api_route_bet9ja/sport/sport_response.json` - Captured Bet9ja API response
- `src/scraping/clients/bet9ja.py` - Existing fetch_sports() implementation
- `src/db/models/competitor.py` - CompetitorTournament model from Phase 13

### Secondary (MEDIUM confidence)
- `src/scraping/orchestrator.py:859-896` - Existing `_extract_football_tournaments` shows Bet9ja parsing pattern
- `src/scraping/clients/sportybet.py` - Existing client to extend

### Verified by codebase inspection
- All API structures verified against captured response files
- Model fields verified against Phase 13 competitor.py
- Existing patterns verified against orchestrator.py
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: SportyBet and Bet9ja REST APIs
- Ecosystem: Existing scraper infrastructure
- Patterns: Tournament discovery, data normalization
- Pitfalls: Missing SR IDs, country name inconsistency

**Confidence breakdown:**
- API structures: HIGH - verified from captured responses
- Architecture: HIGH - follows existing codebase patterns
- Pitfalls: HIGH - derived from CONTEXT.md and API analysis
- Code examples: HIGH - based on existing client implementations

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - API structures stable)
</metadata>

---

*Phase: 14-tournament-discovery-scraping*
*Research completed: 2026-01-23*
*Ready for planning: yes*
