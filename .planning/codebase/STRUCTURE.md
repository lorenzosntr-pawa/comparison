# Codebase Structure

**Analysis Date:** 2026-01-20

## Directory Layout

```
mvp/
├── mapping_markets/          # TypeScript market mapping library
│   ├── src/                 # Source code
│   │   ├── mappers/        # Transformation logic
│   │   ├── types/          # Type definitions
│   │   ├── mappings/       # Lookup tables
│   │   └── utils/          # Utility functions
│   ├── dist/               # Compiled output
│   ├── jsons_examples/     # Sample API responses
│   └── .planning/          # Phase planning docs
├── scraper/                 # Python scraper CLI tools
│   ├── src/                # Source code
│   │   ├── sportybet_scraper/
│   │   ├── betpawa_scraper/
│   │   └── bet9ja_scraper/
│   └── responses_examples/ # Sample responses
└── .planning/              # Root project planning
    └── codebase/          # This documentation
```

## Directory Purposes

**mapping_markets/src/mappers/:**
- Purpose: Market transformation logic
- Contains: Platform-specific mappers, unified dispatcher
- Key files: `unified.ts`, `sportybet-to-betpawa.ts`, `bet9ja-to-betpawa.ts`
- Tests: Co-located `*.test.ts` and `*.integration.test.ts` files

**mapping_markets/src/types/:**
- Purpose: TypeScript type definitions
- Contains: Interfaces for each platform, error types, mapped output types
- Key files: `sportybet.ts`, `betpawa.ts`, `bet9ja.ts`, `errors.ts`, `mapped.ts`, `competitors.ts`
- Tests: `errors.test.ts`

**mapping_markets/src/mappings/:**
- Purpose: Static lookup tables
- Contains: 111+ market mappings with outcome mappings
- Key files: `market-ids.ts` (single file with all mappings)
- Tests: `market-ids.test.ts`

**mapping_markets/src/utils/:**
- Purpose: Parsing and validation utilities
- Contains: Specifier parser, Bet9ja key parser, input validators
- Key files: `specifier-parser.ts`, `bet9ja-parser.ts`, `validate-input.ts`
- Tests: Co-located `*.test.ts` files

**scraper/src/sportybet_scraper/:**
- Purpose: SportyBet API scraper CLI
- Contains: CLI commands, HTTP client, configuration
- Key files: `cli.py`, `client.py`, `config.py`, `exceptions.py`
- Entry: `sportybet-scraper` command

**scraper/src/betpawa_scraper/:**
- Purpose: BetPawa API scraper CLI (source of truth)
- Contains: CLI commands, HTTP client, models, configuration
- Key files: `cli.py`, `client.py`, `config.py`, `models.py`
- Entry: `betpawa-scraper` command

**scraper/src/bet9ja_scraper/:**
- Purpose: Bet9ja API scraper CLI
- Contains: CLI commands, HTTP client, models, configuration
- Key files: `cli.py`, `client.py`, `config.py`, `models.py`
- Entry: `bet9ja-scraper` command

## Key File Locations

**Entry Points:**
- `mapping_markets/src/index.ts` - Library export entry point
- `scraper/src/sportybet_scraper/cli.py` - SportyBet CLI
- `scraper/src/betpawa_scraper/cli.py` - BetPawa CLI
- `scraper/src/bet9ja_scraper/cli.py` - Bet9ja CLI

**Configuration:**
- `mapping_markets/tsconfig.json` - TypeScript compiler config
- `mapping_markets/jest.config.js` - Test runner config
- `mapping_markets/package.json` - Dependencies, scripts
- `scraper/pyproject.toml` - Python project config, CLI entry points
- `scraper/src/*/config.py` - Per-scraper API configuration

**Core Logic:**
- `mapping_markets/src/mappers/unified.ts` - Multi-source dispatcher
- `mapping_markets/src/mappers/sportybet-to-betpawa.ts` - SportyBet mapper
- `mapping_markets/src/mappers/bet9ja-to-betpawa.ts` - Bet9ja mapper
- `mapping_markets/src/mappings/market-ids.ts` - 111+ market mappings

**Testing:**
- `mapping_markets/src/**/*.test.ts` - Unit tests (co-located)
- `mapping_markets/src/**/*.integration.test.ts` - Integration tests
- `mapping_markets/jsons_examples/` - Sample API responses for testing

**Documentation:**
- `mapping_markets/README.md` - Library overview, quick start
- `mapping_markets/USAGE.md` - Full API reference
- `mapping_markets/ADDING-MARKETS.md` - Guide for extending mappings
- `scraper/README.md` - Scraper overview, CLI commands

## Naming Conventions

**Files:**
- kebab-case.ts - TypeScript modules (`bet9ja-to-betpawa.ts`)
- snake_case.py - Python modules (`sportybet_scraper`)
- *.test.ts - Unit test files (co-located with source)
- *.integration.test.ts - Integration test files
- UPPERCASE.md - Important docs (README, USAGE, ADDING-MARKETS)

**Directories:**
- kebab-case - Feature directories
- snake_case - Python package directories
- Plural names for collections (`mappers/`, `types/`, `utils/`)

**Special Patterns:**
- index.ts - Barrel exports for directories
- __init__.py - Python package markers
- __main__.py - Python module entry points
- config.py - Configuration per scraper

## Where to Add New Code

**New Market Mapping:**
- Add to `mapping_markets/src/mappings/market-ids.ts` (MARKET_MAPPINGS array)
- Add tests to `mapping_markets/src/mappings/market-ids.test.ts`
- Follow guide: `mapping_markets/ADDING-MARKETS.md`

**New Mapper Logic:**
- Implementation: `mapping_markets/src/mappers/{platform}-to-betpawa.ts`
- Tests: Same directory with `.test.ts` suffix
- Export from: `mapping_markets/src/mappers/index.ts`

**New Type Definitions:**
- Implementation: `mapping_markets/src/types/{name}.ts`
- Export from: `mapping_markets/src/types/index.ts`

**New Utility Function:**
- Implementation: `mapping_markets/src/utils/{name}.ts`
- Tests: Same directory with `.test.ts` suffix
- Export from: `mapping_markets/src/utils/index.ts`

**New Scraper:**
- Create: `scraper/src/{platform}_scraper/`
- Include: `__init__.py`, `__main__.py`, `cli.py`, `client.py`, `config.py`
- Register in: `scraper/pyproject.toml` under [project.scripts]

## Special Directories

**mapping_markets/dist/:**
- Purpose: Compiled TypeScript output
- Source: Auto-generated by TypeScript compiler
- Committed: No (in .gitignore)

**mapping_markets/jsons_examples/:**
- Purpose: Sample API responses for development and testing
- Source: Captured from actual API calls
- Committed: Yes (reference data)

**mapping_markets/.planning/:**
- Purpose: Phase planning documentation
- Source: GSD workflow artifacts
- Committed: Yes (project history)

---

*Structure analysis: 2026-01-20*
*Update when directory structure changes*
