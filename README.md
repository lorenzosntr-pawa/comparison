# Betpawa Odds Comparison Tool

A comparative analysis tool (branded "pawaRisk") for Betpawa to analyze and compare its football markets and odds with competitors (SportyBet, Bet9ja). The tool scrapes odds data on a schedule, matches events across platforms using SportRadar IDs, and displays side-by-side comparisons with margin analysis through a React web interface.

## Features

- **Real-time odds scraping** from BetPawa, SportyBet, and Bet9ja
- **Cross-platform event matching** using SportRadar IDs (99.9% accuracy)
- **Side-by-side odds comparison** with color-coded indicators
- **Margin analysis** showing Betpawa vs competitors
- **Historical odds tracking** with interactive charts
- **WebSocket-powered live updates** for scrape progress and odds changes
- **Configurable scraping schedule** and data retention (1-90 days)
- **Coverage analysis** with tournament/event availability metrics
- **Market grouping** by BetPawa categories (Popular, Goals, Handicaps, etc.)
- **Fuzzy search** for quick market filtering

## Architecture

### Backend (Python/FastAPI)

The backend is organized into focused modules:

```
src/
├── api/              # FastAPI routes, schemas, WebSocket
├── caching/          # In-memory odds cache (97% latency reduction)
├── db/               # SQLAlchemy 2.0 models, PostgreSQL
├── market_mapping/   # 128 market ID mappings across platforms
├── matching/         # Event matching service
├── scheduling/       # APScheduler background jobs
├── scraping/         # Event-centric parallel scrapers
└── storage/          # Async write pipeline with change detection
```

**Key patterns:**
- Event-centric parallel scraping (all platforms per event simultaneously)
- In-memory cache with frozen dataclasses for fast API responses
- Async write queue with change detection for efficient DB persistence
- WebSocket topic subscriptions for real-time updates

### Frontend (React/Vite)

The frontend uses feature-based organization:

```
web/src/
├── features/         # Feature modules (dashboard, matches, odds-comparison, etc.)
├── hooks/            # Shared React hooks (WebSocket, data fetching)
├── lib/              # API client, utilities
├── components/       # Reusable UI components (shadcn/ui)
└── types/            # TypeScript definitions
```

**Key patterns:**
- TanStack Query v5 for server state management
- WebSocket hooks for real-time updates
- shadcn/ui component library with Tailwind CSS v4
- recharts for historical data visualization

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ with pnpm
- PostgreSQL 14+

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .

# Set up database
createdb betpawa_comparison
alembic upgrade head

# Start server
uvicorn src.api.app:create_app --factory --reload
```

The API server starts at `http://localhost:8000`.

### Frontend Setup

```bash
cd web
pnpm install
pnpm dev
```

The frontend starts at `http://localhost:5173`.

## Development

### Running Tests

```bash
# Backend tests
pytest

# Frontend (from web/ directory)
pnpm lint
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Style

- **Backend:** Python with Pydantic v2, SQLAlchemy 2.0 async
- **Frontend:** TypeScript strict mode, React 19

## Project Structure

```
.
├── src/                    # Python backend
│   ├── api/               # FastAPI routes, schemas, WebSocket
│   ├── caching/           # In-memory cache layer
│   ├── db/                # SQLAlchemy models
│   ├── market_mapping/    # Market ID normalization
│   ├── matching/          # Event matching service
│   ├── scheduling/        # APScheduler jobs
│   ├── scraping/          # Scraper clients and coordination
│   └── storage/           # Async write pipeline
├── web/                    # React frontend
│   └── src/
│       ├── features/      # Feature modules
│       ├── hooks/         # Shared React hooks
│       ├── lib/           # API client, utilities
│       ├── components/    # UI components
│       └── types/         # TypeScript definitions
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
├── tests/                 # Backend tests
└── .planning/             # Project planning documentation
```

## Configuration

Settings are configurable via the Settings page in the UI or via API:

| Setting | Description | Default |
|---------|-------------|---------|
| Scrape interval | Minutes between automatic scrapes | 5 |
| Odds retention | Days to keep historical odds | 7 |
| Runs retention | Days to keep scrape run logs | 3 |
| Cleanup frequency | Hours between cleanup jobs | 24 |
| Max concurrent events | Parallel events per scrape batch | 10 |

## API Documentation

FastAPI auto-generates OpenAPI documentation at `/docs` when running locally.

### Key Endpoints

- `GET /api/events` - List events with odds
- `GET /api/events/{id}` - Event details with all markets
- `GET /api/scrape-runs` - Scrape history
- `POST /api/scrape/event/{sr_id}` - Trigger single event scrape
- `GET /api/history/odds` - Historical odds data
- `GET /api/history/margins` - Historical margin data
- `WS /api/ws` - WebSocket for real-time updates

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL with asyncpg
- APScheduler
- structlog for logging

### Frontend
- React 19
- Vite 7
- TypeScript 5.9
- TanStack Query v5
- Tailwind CSS v4
- shadcn/ui components
- recharts for charts

## License

Internal Betpawa tool - proprietary.
