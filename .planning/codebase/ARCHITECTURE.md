# Architecture

**Analysis Date:** 2026-01-20

## Pattern Overview

**Overall:** Polyglot Data-Transformation Pipeline (TypeScript + Python)

**Key Characteristics:**
- Two-tier architecture: Scrapers (Python) + Mapping Library (TypeScript)
- Stateless data transformation
- CLI-based scraper tools with JSON output
- Zero-dependency TypeScript library for market mapping
- Cross-platform event matching via SportRadar IDs

## Layers

**Scraper Layer (Python):**
- Purpose: Extract raw odds data from external betting APIs
- Contains: CLI tools, HTTP clients, retry logic
- Location: `scraper/src/sportybet_scraper/`, `scraper/src/betpawa_scraper/`, `scraper/src/bet9ja_scraper/`
- Depends on: httpx, click, tenacity
- Used by: External orchestration (manual or automated)

**Type/Model Layer:**
- Purpose: Define data structures for each platform
- Contains: TypeScript interfaces, Python dataclasses
- Location: `mapping_markets/src/types/`, `scraper/src/*/models.py`
- Depends on: Nothing (pure type definitions)
- Used by: Mappers, clients

**Mapping/Transformation Layer (TypeScript):**
- Purpose: Transform competitor market data into Betpawa format
- Contains: Platform-specific mappers, unified dispatcher
- Location: `mapping_markets/src/mappers/`
- Depends on: Types, mappings, utilities
- Used by: Downstream consumers of normalized market data

**Lookup/Data Layer:**
- Purpose: Static lookup table mapping market IDs across platforms
- Contains: 111+ market mappings with outcome mappings
- Location: `mapping_markets/src/mappings/market-ids.ts`
- Depends on: Types
- Used by: Mappers

**Utility Layer:**
- Purpose: Parsing, validation, type guards
- Contains: Specifier parsers, input validators
- Location: `mapping_markets/src/utils/`
- Depends on: Types
- Used by: Mappers

## Data Flow

**Complete Pipeline:**

1. **Scraper Execution** (Python CLI)
   - User runs: `sportybet-scraper scrape <event_id>` or similar
   - CLI parses args via Click
   - HTTP client fetches data with retry (tenacity)
   - Output: JSON file with raw API response

2. **Market Transformation** (TypeScript Library)
   - Input: `CompetitorInput` discriminated union
   - Router: `mapToBetpawa()` dispatches to platform-specific mapper
   - Lookup: Find mapping by sportybetId or bet9jaKey
   - Parse: Extract specifiers (handicap, total lines)
   - Map: Transform outcomes to Betpawa format
   - Output: `MappedMarket` or `MappingResult<MappedMarket>`

**Cross-Platform Matching:**
- SportRadar event IDs enable cross-platform event matching
- SportyBet: Uses `eventId` directly
- BetPawa: Extracts from `widgets` array with `type=SPORTRADAR`
- Bet9ja: Extracts from `EXTID` field

**State Management:**
- Stateless: No persistent state
- File-based: Scraper outputs JSON files
- Each transformation is independent

## Key Abstractions

**Discriminated Union for Multi-Source Data:**
- Purpose: Type-safe routing without instanceof checks
- Example: `CompetitorInput = { source: "sportybet", data: SportybetMarket } | { source: "bet9ja", data: Bet9jaInput }`
- Location: `mapping_markets/src/types/competitors.ts`
- Pattern: TypeScript narrows type based on source field

**Factory Pattern for HTTP Clients:**
- Purpose: Centralized HTTP client configuration
- Example: `create_client()` returns configured httpx.Client
- Location: `scraper/src/*/client.py`
- Pattern: Factory function with preset headers, timeouts

**Decorator-Based Retry Logic:**
- Purpose: Retry logic decoupled from business logic
- Example: `@retry(...)` decorator on fetch functions
- Location: `scraper/src/*/client.py`
- Pattern: tenacity decorators with exponential backoff

**Error Result Type:**
- Purpose: Structured error handling without exceptions
- Example: `MappingResult<T> = { success: true, data: T } | { success: false, error: MappingError }`
- Location: `mapping_markets/src/types/errors.ts`
- Pattern: Discriminated union forcing error handling

**Static Lookup Table:**
- Purpose: Single source of truth for market mappings
- Example: `MARKET_MAPPINGS[]` with findByBetpawaId, findBySportybetId, etc.
- Location: `mapping_markets/src/mappings/market-ids.ts`
- Pattern: Array with multiple index functions (O(n) lookup)

## Entry Points

**TypeScript Library:**
- Location: `mapping_markets/src/index.ts`
- Triggers: Import by consuming application
- Responsibilities: Re-export public API (mappers, types, utilities)

**Python CLI Scrapers:**
- Location: `scraper/src/sportybet_scraper/cli.py`, `scraper/src/betpawa_scraper/cli.py`, `scraper/src/bet9ja_scraper/cli.py`
- Triggers: CLI invocation (`sportybet-scraper`, `betpawa-scraper`, `bet9ja-scraper`)
- Responsibilities: Parse args, execute commands, output JSON

## Error Handling

**Strategy:** Return Result types in TypeScript, throw custom exceptions in Python

**TypeScript Patterns:**
- `MappingResult<T>` discriminated union for expected failures
- Error codes: UNKNOWN_MARKET, UNSUPPORTED_PLATFORM, INVALID_SPECIFIER, etc.
- Detailed error context in `MappingError` objects
- Helper functions: `success()`, `failure()`, `createMappingError()`

**Python Patterns:**
- Custom exceptions: `ApiError`, `InvalidEventIdError`, `NetworkError`
- Try/catch at client boundary for HTTP errors
- tenacity handles transient failures automatically

## Cross-Cutting Concerns

**Logging:**
- Python: Structured logging via `logging_config.py` in each scraper
- TypeScript: No logging in library (pure transformation)

**Validation:**
- TypeScript: Type guards (`isSportybetMarket`, `isValidBet9jaEntry`)
- TypeScript: Validation utilities in `src/utils/validate-*.ts`
- Python: Response structure validation in clients

**Retry/Resilience:**
- All scrapers: 3 attempts, exponential backoff (2x multiplier)
- Min wait: 1 second, Max wait: 10 seconds
- Configured in `config.py` files

---

*Architecture analysis: 2026-01-20*
*Update when major patterns change*
