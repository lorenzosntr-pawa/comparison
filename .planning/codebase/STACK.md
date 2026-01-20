# Technology Stack

**Analysis Date:** 2026-01-20

## Languages

**Primary:**
- TypeScript 5.9.3 - All application code in `mapping_markets/`
- Python 3.10+ - Scraper modules in `scraper/`

**Secondary:**
- JavaScript - Build scripts, config files

## Runtime

**Environment:**
- Node.js - JavaScript runtime for mapping_markets library
- Python 3.10+ - Required for scraper applications
- Target ES2020 - TypeScript compilation target

**Package Manager:**
- npm - Package manager for Node.js projects
- Lockfile: `mapping_markets/package-lock.json` present
- setuptools - Python package management via `scraper/pyproject.toml`

## Frameworks

**Core:**
- None (vanilla Node.js library + Python CLI tools)

**Testing:**
- Jest 30.2.0 - Unit tests for TypeScript - `mapping_markets/package.json`
- ts-jest 29.4.6 - TypeScript support for Jest - `mapping_markets/package.json`

**Build/Dev:**
- TypeScript 5.9.3 - Compilation to JavaScript - `mapping_markets/tsconfig.json`
- Babel 7.28.6 - JavaScript transpiler (dev dependency via Jest)

**CLI (Python):**
- click 8.1+ - CLI framework for scrapers - `scraper/pyproject.toml`
- httpx 0.27+ - Async HTTP client library - `scraper/pyproject.toml`
- tenacity 8.2+ - Retry library for fault tolerance - `scraper/pyproject.toml`

## Key Dependencies

**TypeScript (No Runtime Dependencies):**
- Zero production dependencies - library is pure TypeScript
- All dependencies are devDependencies (Jest, TypeScript, types)

**Python Scraper Dependencies:**
- httpx >=0.27 - HTTP requests with async support - `scraper/src/*/client.py`
- click >=8.1 - CLI argument parsing - `scraper/src/*/cli.py`
- tenacity >=8.2 - Exponential backoff retry logic - `scraper/src/*/client.py`

## Configuration

**Environment:**
- No environment variables required
- All configuration hardcoded in config files
- No .env files detected

**Build:**
- `mapping_markets/tsconfig.json` - TypeScript compiler options (strict mode, ES2020, CommonJS)
- `mapping_markets/jest.config.js` - Jest with ts-jest preset
- `scraper/pyproject.toml` - Python project config with CLI entry points

**Scraper Configuration:**
- `scraper/src/sportybet_scraper/config.py` - Base URL, headers, timeout (30s), retry settings
- `scraper/src/betpawa_scraper/config.py` - Base URL, brand headers, timeout settings
- `scraper/src/bet9ja_scraper/config.py` - Base URL, headers, timeout settings

## Platform Requirements

**Development:**
- macOS/Linux/Windows (any platform with Node.js and Python)
- Node.js for TypeScript library
- Python 3.10+ for scrapers
- No external dependencies (no Docker, database, etc.)

**Production:**
- TypeScript library: Distributed as npm package or local module
- Python scrapers: Installed via `pip install -e .`
- CLI registration via pyproject.toml scripts

---

*Stack analysis: 2026-01-20*
*Update after major dependency changes*
